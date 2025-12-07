Deployment samples for the FTTH Management System.

Systemd:
- Copy `deploy/systemd/ftth.service` to `/etc/systemd/system/ftth.service`
- Update `User`/`Group` and paths to venv as appropriate
- `sudo systemctl daemon-reload`
- `sudo systemctl enable --now ftth`

Presentation note (demo only):
- To install the demo systemd services (this will start the backend and the bot at boot), copy the service unit files and enable them using the convenience script included below. These services are intended for a short-lived presentation only. After the demo, remember to disable and remove them to avoid exposing services on a production system.

- Install and start the demo services (runs sudo):

	cd deploy/systemd && sudo ./install_demo_services.sh

- To remove the demo services after the presentation:

	cd deploy/systemd && sudo ./uninstall_demo_services.sh

Note: The scripts will copy `ftth.service` and `bot.service` to `/etc/systemd/system/ftth.service` and `/etc/systemd/system/ftth-bot.service` respectively, enable them, and start them. The uninstall script will disable and remove them.

Nginx:
- Copy `deploy/nginx/ftth.conf` into `/etc/nginx/sites-available/ftth` and symlink to `sites-enabled`.
- Update `server_name` and SSL cert paths (Let's Encrypt or custom certs).
- `sudo systemctl reload nginx`

Fail2Ban:
- Copy `deploy/fail2ban/uvicorn-filter.conf` into `/etc/fail2ban/filter.d/` and `deploy/fail2ban/uvicorn-jail.conf` into `/etc/fail2ban/jail.d/` or `/etc/fail2ban/jail.local`
- Adjust `logpath` to your project path and restart fail2ban: `sudo systemctl restart fail2ban`

Notes:
- These are starting point templates. Validate paths and permissions on your production server.
- Make sure the `logs/ftth.log` has appropriate permissions to be read by fail2ban.
