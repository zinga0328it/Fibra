# 🔄 FTTH Daily Workflow - Checklist Operativo

## 🌅 Morning Check (8:00 - 9:00)

### System Health Check
- [ ] **Backend Status**: `sudo systemctl status ftth`
- [ ] **Database**: `sudo systemctl status postgresql`
- [ ] **Apache**: `sudo systemctl status apache2`
- [ ] **Yggdrasil**: `sudo systemctl status yggdrasil`
- [ ] **Telegram Bot**: `sudo systemctl status telegram-bot`

### Network Verification
- [ ] **Yggdrasil Interface**: `ip addr show ygg0`
- [ ] **Backend Connectivity**: `ping6 200:421e:6385:4a8b:dca7:cfb:197f:e9c3`
- [ ] **Frontend HTTPS**: `curl -I https://servicess.net/fibra/`
- [ ] **Firewall Rules**: `sudo nft list ruleset | grep fibra`

### Log Review
- [ ] **Application Logs**: `tail -50 logs/ftth.log`
- [ ] **System Logs**: `sudo journalctl -u ftth --since "yesterday" | head -20`
- [ ] **Security Events**: `sudo tail -20 /var/log/fail2ban.log`
- [ ] **Backup Status**: `ls -la /opt/ftth/backups/ | tail -5`

## 🚀 Operations (9:00 - 12:00)

### Work Requests Monitoring
- [ ] **New WR Count**: Check API `/works?status=pending`
- [ ] **Technician Assignments**: Review assignments
- [ ] **SLA Compliance**: Check overdue WR
- [ ] **Completion Rate**: Daily statistics

### System Performance
- [ ] **API Response Time**: Monitor latency
- [ ] **Database Queries**: Check slow queries
- [ ] **Memory Usage**: `free -h`
- [ ] **Disk Space**: `df -h`

### User Support
- [ ] **Telegram Messages**: Check bot notifications
- [ ] **Support Requests**: Review pending issues
- [ ] **User Feedback**: Monitor satisfaction

## 🍽️ Lunch Break (12:00 - 13:00)

## 🔧 Maintenance (13:00 - 17:00)

### Security Updates
- [ ] **SSL Certificates**: `certbot certificates`
- [ ] **System Updates**: `sudo apt update && sudo apt list --upgradable`
- [ ] **Firewall Rules**: Review and optimize
- [ ] **Fail2Ban Status**: `sudo fail2ban-client status`

### Data Management
- [ ] **Database Cleanup**: Remove old logs
- [ ] **Backup Verification**: Test restore procedure
- [ ] **Analytics Update**: Refresh KPI data
- [ ] **Archive Old Data**: Move to cold storage

### Performance Optimization
- [ ] **Log Rotation**: Check log sizes
- [ ] **Cache Clearing**: Clean temporary files
- [ ] **Service Restart**: Rolling restart if needed
- [ ] **Resource Monitoring**: Identify bottlenecks

## 📊 Reporting (17:00 - 18:00)

### Daily Report
- [ ] **WR Processed**: Count completed work
- [ ] **System Uptime**: 99.9% target
- [ ] **Error Rate**: <1% target
- [ ] **User Satisfaction**: Monitor feedback

### Issue Resolution
- [ ] **Open Tickets**: Close resolved issues
- [ ] **Follow-ups**: Contact users if needed
- [ ] **Documentation**: Update procedures
- [ ] **Prevention**: Implement fixes

## 🌙 Evening Check (18:00 - 19:00)

### Final Verification
- [ ] **All Services**: Green status
- [ ] **Backup Complete**: Today's backup successful
- [ ] **No Alerts**: Clean monitoring dashboard
- [ ] **Tomorrow Prep**: Review calendar

### Handover Notes
- [ ] **Issues to Watch**: Note any concerns
- [ ] **Planned Changes**: Document upcoming work
- [ ] **Contact Info**: Update emergency contacts
- [ ] **Documentation**: Commit any changes

---

## 🚨 Emergency Procedures

### If System Down
1. **Check Services**: `sudo systemctl --failed`
2. **View Logs**: `sudo journalctl -u ftth -f`
3. **Restart Services**: `sudo systemctl restart ftth`
4. **Contact Support**: Use emergency contacts

### If Security Alert
1. **Isolate**: Disconnect suspicious connections
2. **Check Logs**: `grep "attack\|breach" logs/*.log`
3. **Update Rules**: Modify firewall if needed
4. **Report**: Document incident

### If Data Loss
1. **Stop Services**: Prevent further damage
2. **Assess Damage**: Check what was lost
3. **Restore Backup**: Use latest backup
4. **Verify Integrity**: Test restored data

---

## 📈 KPIs to Monitor

- **System Uptime**: >99.9%
- **API Response Time**: <500ms
- **Error Rate**: <1%
- **WR Processing Time**: <4 hours average
- **User Satisfaction**: >95%
- **Security Incidents**: 0 per month

---

*Questo workflow è integrato con il sistema Obsidian Canvas. Usa `FTTH-Index.canvas` per navigazione interattiva.*