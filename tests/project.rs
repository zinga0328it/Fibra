use ftth_lia_mcp::project::{DiffInput, ProjectServer};
use std::{fs, os::unix::fs::symlink};

fn fixture() -> (tempfile::TempDir, ProjectServer) {
    let root = tempfile::tempdir().unwrap();
    fs::create_dir(root.path().join("src")).unwrap();
    fs::write(root.path().join("src/lib.rs"), "original\n").unwrap();
    let server = ProjectServer::open(root.path()).unwrap();
    (root, server)
}

#[test]
fn reads_and_hash_bound_diff_never_write() {
    let (_root, server) = fixture();
    let before = server.read("src/lib.rs").unwrap();
    assert!(before.read_only);
    assert_eq!(before.sha256.len(), 64);
    let diff = server
        .diff(DiffInput {
            path: before.path.clone(),
            expected_sha256: before.sha256.clone(),
            proposed_content: "proposed\n".into(),
        })
        .unwrap();
    assert!(diff.diff.contains("-original\n+proposed"));
    assert!(diff.read_only);
    assert_eq!(server.read("src/lib.rs").unwrap().content, before.content);
    assert!(
        server
            .diff(DiffInput {
                path: before.path,
                expected_sha256: "stale".into(),
                proposed_content: "proposed\n".into()
            })
            .is_err()
    );
}

#[test]
fn traversal_hidden_files_secrets_and_absolute_paths_are_denied() {
    let (_root, server) = fixture();
    for path in [
        "",
        "../src/lib.rs",
        "/home/aaa/fibra/app/main.py",
        "src/../Cargo.toml",
        "src/./lib.rs",
        "src//lib.rs",
        "src\\lib.rs",
        "src/%2e%2e/lib.rs",
        ".env",
        ".git/config",
        ".cargo/config.toml",
        ".github/workflows/a.yml",
        "src/.hidden.rs",
        "src/credentials.rs",
        "src/password.rs",
        "target/a.rs",
        "src/lib.rs\0",
    ] {
        assert!(server.read(path).is_err(), "{path:?} escaped allowlist");
    }
}

#[test]
fn symlinks_and_hardlinks_are_rejected_even_inside_root() {
    let (root, server) = fixture();
    let outside = tempfile::tempdir().unwrap();
    fs::write(outside.path().join("private.rs"), "private-outside-data").unwrap();
    symlink(
        outside.path().join("private.rs"),
        root.path().join("src/outside.rs"),
    )
    .unwrap();
    symlink(
        root.path().join("src/lib.rs"),
        root.path().join("src/inside.rs"),
    )
    .unwrap();
    symlink(outside.path(), root.path().join("src/nested")).unwrap();
    fs::hard_link(
        outside.path().join("private.rs"),
        root.path().join("src/hard.rs"),
    )
    .unwrap();
    for path in [
        "src/outside.rs",
        "src/inside.rs",
        "src/nested/private.rs",
        "src/hard.rs",
    ] {
        assert!(server.read(path).is_err(), "{path}");
    }
    let root_link = outside.path().join("root-link");
    symlink(root.path(), &root_link).unwrap();
    assert!(ProjectServer::open(&root_link).is_err());
}

#[test]
fn opened_root_is_pinned_after_path_replacement() {
    let container = tempfile::tempdir().unwrap();
    let original = container.path().join("original");
    let moved = container.path().join("moved");
    let outside = container.path().join("outside");
    fs::create_dir_all(original.join("src")).unwrap();
    fs::create_dir_all(outside.join("src")).unwrap();
    fs::write(original.join("src/lib.rs"), "safe").unwrap();
    fs::write(outside.join("src/lib.rs"), "private-outside-data").unwrap();
    let server = ProjectServer::open(&original).unwrap();
    fs::rename(&original, &moved).unwrap();
    symlink(&outside, &original).unwrap();
    assert_eq!(server.read("src/lib.rs").unwrap().content, "safe");
}

#[test]
fn racing_directory_symlinks_never_expose_outside_content() {
    let (root, server) = fixture();
    let outside = tempfile::tempdir().unwrap();
    fs::write(outside.path().join("lib.rs"), "private-outside-data").unwrap();
    let source = root.path().join("src");
    let saved = root.path().join("saved");
    let external = outside.path().to_owned();
    let racer = std::thread::spawn(move || {
        for _attempt in 0..200 {
            fs::rename(&source, &saved).unwrap();
            symlink(&external, &source).unwrap();
            fs::remove_file(&source).unwrap();
            fs::rename(&saved, &source).unwrap();
        }
    });
    for _attempt in 0..500 {
        if let Ok(read) = server.read("src/lib.rs") {
            assert_eq!(read.content, "original\n");
        }
    }
    racer.join().unwrap();
}

#[test]
fn binary_large_and_special_files_are_refused() {
    let (root, server) = fixture();
    fs::write(root.path().join("src/large.rs"), vec![b'x'; 128 * 1024 + 1]).unwrap();
    fs::write(root.path().join("src/binary.rs"), [0_u8, 255]).unwrap();
    let _socket =
        std::os::unix::net::UnixListener::bind(root.path().join("src/socket.rs")).unwrap();
    for path in ["src/large.rs", "src/binary.rs", "src/socket.rs"] {
        assert!(server.read(path).is_err());
    }
    let before = server.read("src/lib.rs").unwrap();
    assert!(
        server
            .diff(DiffInput {
                path: before.path,
                expected_sha256: before.sha256,
                proposed_content: "x".repeat(128 * 1024 + 1)
            })
            .is_err()
    );
}
