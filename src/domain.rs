#[derive(Clone, Debug, PartialEq)]
pub struct Work {
    pub id: u64,
    pub numero_wr: String,
    pub indirizzo: String,
    pub nome_cliente: String,
    pub tipo_lavoro: String,
    pub stato: String,
}

#[derive(Clone, Debug, PartialEq)]
pub struct Material {
    pub id: u64,
    pub nome: String,
    pub codice: String,
    pub descrizione: String,
    pub tipo: String,
    pub quantita: u64,
}

#[derive(Clone, Debug, PartialEq)]
pub enum Document {
    Work(Work),
    Material(Material),
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum ReadError {
    InvalidInput,
    NotFound,
    Ambiguous,
    Unauthorized,
    Unavailable,
}

impl ReadError {
    pub fn code(self) -> &'static str {
        match self {
            Self::InvalidInput => "invalid_input",
            Self::NotFound => "not_found",
            Self::Ambiguous => "ambiguous",
            Self::Unauthorized => "unauthorized",
            Self::Unavailable => "unavailable",
        }
    }
}

pub trait ReadBackend: Send + Sync {
    fn search(&self, query: &str, limit: usize) -> Result<Vec<Document>, ReadError>;
    fn fetch(&self, document_id: &str) -> Result<Document, ReadError>;
    fn find_wr(&self, numero_wr: &str) -> Result<Work, ReadError>;
    fn counts(&self) -> Result<Vec<(String, usize)>, ReadError>;
    fn health(&self) -> Result<(), ReadError>;
}

#[derive(Clone)]
pub struct MockBackend {
    works: Vec<Work>,
    materials: Vec<Material>,
    authorized: bool,
    available: bool,
}

impl Default for MockBackend {
    fn default() -> Self {
        Self {
            works: vec![
                Work {
                    id: 7,
                    numero_wr: "103579742".into(),
                    indirizzo: "Via di Prova 1".into(),
                    nome_cliente: "Cliente Simulato Alfa".into(),
                    tipo_lavoro: "attivazione".into(),
                    stato: "aperto".into(),
                },
                Work {
                    id: 8,
                    numero_wr: "000000002".into(),
                    indirizzo: "Via di Prova 2".into(),
                    nome_cliente: "Cliente Simulato Beta".into(),
                    tipo_lavoro: "manutenzione".into(),
                    stato: "chiuso".into(),
                },
            ],
            materials: vec![Material {
                id: 3,
                nome: "ONT Simulato".into(),
                codice: "TEST-ONT-003".into(),
                descrizione: "Materiale fittizio per test locali".into(),
                tipo: "ONT".into(),
                quantita: 4,
            }],
            authorized: true,
            available: true,
        }
    }
}

impl ReadBackend for MockBackend {
    fn health(&self) -> Result<(), ReadError> {
        if !self.authorized {
            return Err(ReadError::Unauthorized);
        }
        if !self.available {
            return Err(ReadError::Unavailable);
        }
        Ok(())
    }

    fn search(&self, query: &str, limit: usize) -> Result<Vec<Document>, ReadError> {
        self.health()?;
        let query = query.trim();
        if query.is_empty()
            || query.len() > 128
            || query.chars().any(char::is_control)
            || !(1..=20).contains(&limit)
        {
            return Err(ReadError::InvalidInput);
        }
        let query = query.to_lowercase();
        let works = self
            .works
            .iter()
            .filter(|work| {
                [
                    &work.numero_wr,
                    &work.indirizzo,
                    &work.nome_cliente,
                    &work.tipo_lavoro,
                ]
                .iter()
                .any(|field| field.to_lowercase().contains(&query))
            })
            .cloned()
            .map(Document::Work);
        let materials = self
            .materials
            .iter()
            .filter(|material| {
                [
                    &material.nome,
                    &material.codice,
                    &material.descrizione,
                    &material.tipo,
                ]
                .iter()
                .any(|field| field.to_lowercase().contains(&query))
            })
            .cloned()
            .map(Document::Material);
        Ok(works.chain(materials).take(limit).collect())
    }

    fn fetch(&self, document_id: &str) -> Result<Document, ReadError> {
        self.health()?;
        let (kind, raw_id) = document_id.split_once('_').ok_or(ReadError::InvalidInput)?;
        if raw_id.is_empty() || !raw_id.bytes().all(|byte| byte.is_ascii_digit()) {
            return Err(ReadError::InvalidInput);
        }
        let id = raw_id.parse::<u64>().map_err(|_| ReadError::InvalidInput)?;
        match kind {
            "work" => self
                .works
                .iter()
                .find(|work| work.id == id)
                .cloned()
                .map(Document::Work)
                .ok_or(ReadError::NotFound),
            "material" => self
                .materials
                .iter()
                .find(|material| material.id == id)
                .cloned()
                .map(Document::Material)
                .ok_or(ReadError::NotFound),
            _ => Err(ReadError::InvalidInput),
        }
    }

    fn find_wr(&self, numero_wr: &str) -> Result<Work, ReadError> {
        self.health()?;
        if numero_wr.is_empty()
            || numero_wr.len() > 32
            || !numero_wr.bytes().all(|byte| byte.is_ascii_digit())
        {
            return Err(ReadError::InvalidInput);
        }
        let mut matches = self.works.iter().filter(|work| work.numero_wr == numero_wr);
        let work = matches.next().ok_or(ReadError::NotFound)?;
        if matches.next().is_some() {
            return Err(ReadError::Ambiguous);
        }
        Ok(work.clone())
    }

    fn counts(&self) -> Result<Vec<(String, usize)>, ReadError> {
        self.health()?;
        let mut counts = std::collections::BTreeMap::new();
        for work in &self.works {
            *counts.entry(work.stato.clone()).or_insert(0) += 1;
        }
        Ok(counts.into_iter().collect())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wr_is_not_the_internal_id() {
        let backend = MockBackend::default();
        assert_eq!(backend.find_wr("103579742").unwrap().id, 7);
        assert_eq!(backend.fetch("work_103579742"), Err(ReadError::NotFound));
        assert_eq!(backend.find_wr("7"), Err(ReadError::NotFound));
        assert_eq!(backend.find_wr("000000002").unwrap().id, 8);
    }

    #[test]
    fn search_covers_works_and_materials_with_a_shared_limit() {
        let backend = MockBackend::default();
        assert_eq!(backend.search("SIMULATO", 20).unwrap().len(), 3);
        assert_eq!(backend.search("simulato", 1).unwrap().len(), 1);
        assert_eq!(backend.search("Via di Prova", 20).unwrap().len(), 2);
        assert_eq!(backend.search("TEST-ONT-003", 20).unwrap().len(), 1);
        assert!(backend.search("inesistente", 20).unwrap().is_empty());
    }

    #[test]
    fn fetch_validates_document_kind_and_identifier() {
        let backend = MockBackend::default();
        assert!(matches!(backend.fetch("work_7"), Ok(Document::Work(_))));
        assert!(matches!(
            backend.fetch("material_3"),
            Ok(Document::Material(_))
        ));
        for input in [
            "7",
            "work_-7",
            "work_",
            "work_7/assign",
            "secret_1",
            "https://example.com",
        ] {
            assert_eq!(backend.fetch(input), Err(ReadError::InvalidInput));
        }
    }

    #[test]
    fn invalid_queries_are_rejected() {
        let backend = MockBackend::default();
        for input in ["", "   ", "bad\nquery"] {
            assert_eq!(backend.search(input, 10), Err(ReadError::InvalidInput));
        }
        assert_eq!(
            backend.search(&"a".repeat(129), 10),
            Err(ReadError::InvalidInput)
        );
        assert_eq!(backend.search("test", 0), Err(ReadError::InvalidInput));
        assert_eq!(backend.search("test", 21), Err(ReadError::InvalidInput));
        for input in ["", "103579742/close", " 103579742", "WR-103579742"] {
            assert_eq!(backend.find_wr(input), Err(ReadError::InvalidInput));
        }
    }

    #[test]
    fn duplicate_wr_is_not_silently_selected() {
        let mut backend = MockBackend::default();
        backend.works.push(backend.works[0].clone());
        assert_eq!(backend.find_wr("103579742"), Err(ReadError::Ambiguous));
    }

    #[test]
    fn authorization_and_outage_fail_closed_for_every_operation() {
        for expected in [ReadError::Unauthorized, ReadError::Unavailable] {
            let backend = MockBackend {
                authorized: expected != ReadError::Unauthorized,
                available: expected != ReadError::Unavailable,
                ..MockBackend::default()
            };
            assert_eq!(backend.health(), Err(expected));
            assert_eq!(backend.search("test", 10), Err(expected));
            assert_eq!(backend.fetch("work_7"), Err(expected));
            assert_eq!(backend.find_wr("103579742"), Err(expected));
            assert_eq!(backend.counts(), Err(expected));
        }
    }

    #[test]
    fn repeated_reads_do_not_change_records() {
        let backend = MockBackend::default();
        let before = backend.fetch("work_7");
        assert_eq!(
            backend.counts().unwrap(),
            vec![("aperto".into(), 1), ("chiuso".into(), 1)]
        );
        for _iteration in 0..3 {
            backend.find_wr("103579742").unwrap();
            backend.search("simulato", 20).unwrap();
        }
        assert_eq!(before, backend.fetch("work_7"));
    }
}
