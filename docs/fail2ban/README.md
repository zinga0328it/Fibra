This directory contains sample fail2ban configuration for monitoring the FTTH API running with uvicorn.

Sample steps to enable:

1. Ensure the application logs to a file (e.g. `logs/ftth.log`).
2. Place the filter configuration into `/etc/fail2ban/filter.d/uvicorn-http.conf`.
3. Place the jail configuration into `/etc/fail2ban/jail.d/ftth-api.conf`.
4. Restart fail2ban: `sudo systemctl restart fail2ban`

Adjust `logpath` and `port` as needed for your server.
