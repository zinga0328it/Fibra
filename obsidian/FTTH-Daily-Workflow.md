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
- [ ] **API Health Check**: `curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/health/"`
- [ ] **Frontend HTTPS**: `curl -I https://servicess.net/fibra/`
- [ ] **Firewall Rules**: `sudo nft list ruleset | grep fibra`

### Log Review
- [ ] **Application Logs**: `tail -50 logs/ftth.log`
- [ ] **System Logs**: `sudo journalctl -u ftth --since "yesterday" | head -20`
- [ ] **Security Events**: `sudo tail -20 /var/log/fail2ban.log`
- [ ] **Backup Status**: `ls -la /opt/ftth/backups/ | tail -5`

## 🚀 Operations (9:00 - 12:00)

### API Endpoints Verification
- [ ] **Works Endpoint**: `curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/" | jq length`
- [ ] **Modems Available**: `curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq length`
- [ ] **ONTs Available**: `curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/onts/" -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq length`
- [ ] **Ingest Endpoints**: Test `/works/ingest/work` e `/works/ingest/bulk`

### Work Requests Monitoring
- [ ] **New WR Count**: Check API `/works?status=aperto`
- [ ] **Technician Assignments**: Review assignments via API
- [ ] **SLA Compliance**: Check overdue WR via stats
- [ ] **Completion Rate**: Daily statistics via `/stats/daily`

### Equipment Tracking
- [ ] **Modems Assigned**: Check modem status via API
- [ ] **ONTs Assigned**: Check ONT status via API
- [ ] **Delivery Status**: Verify equipment deliveries
- [ ] **Installation Notes**: Review technician notes

### System Performance
- [ ] **API Response Time**: Monitor latency with curl timing
- [ ] **Database Queries**: Check slow queries in logs
- [ ] **Memory Usage**: `free -h`
- [ ] **Disk Space**: `df -h`

### User Support
- [ ] **Telegram Messages**: Check bot notifications
- [ ] **Support Requests**: Review pending issues
- [ ] **User Feedback**: Monitor satisfaction
- [ ] **Web Interface**: Test gestionale.html accessibility

## 🍽️ Lunch Break (12:00 - 13:00)

## 🔧 Maintenance (13:00 - 17:00)

### Security Updates
- [ ] **SSL Certificates**: `certbot certificates`
- [ ] **System Updates**: `sudo apt update && sudo apt list --upgradable`
- [ ] **Firewall Rules**: Review and optimize Yggdrasil rules
- [ ] **Fail2Ban Status**: `sudo fail2ban-client status`
- [ ] **API Keys**: Verify API key validity

### Data Management
- [ ] **Database Cleanup**: Remove old logs and temp files
- [ ] **Backup Verification**: Test restore procedure
- [ ] **Analytics Update**: Refresh KPI data via `/stats/`
- [ ] **Archive Old Data**: Move completed works to archive

### Performance Optimization
- [ ] **Log Rotation**: Check log sizes in `/logs/`
- [ ] **Cache Clearing**: Clean temporary files
- [ ] **Service Restart**: Rolling restart if needed
- [ ] **Resource Monitoring**: Identify bottlenecks

### Equipment Maintenance
- [ ] **Modem Inventory**: Verify all modems are tracked
- [ ] **ONT Inventory**: Verify all ONTs are tracked
- [ ] **Equipment Status**: Check for faulty equipment
- [ ] **Stock Levels**: Monitor available equipment

## 📊 Reporting (17:00 - 18:00)

### Daily Report
- [ ] **WR Processed**: Count completed work via API
- [ ] **Equipment Installed**: Count modem/ONT installations
- [ ] **System Uptime**: 99.9% target
- [ ] **API Availability**: 100% target
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
- [ ] **Equipment Sync**: All equipment properly tracked
- [ ] **Tomorrow Prep**: Review calendar

### Handover Notes
- [ ] **Issues to Watch**: Note any concerns
- [ ] **Planned Changes**: Document upcoming work
- [ ] **Contact Info**: Update emergency contacts
- [ ] **API Documentation**: Commit any endpoint changes
- [ ] **Equipment Status**: Document current inventory

---

## 🚨 Emergency Procedures

### If System Down
1. **Check Services**: `sudo systemctl --failed`
2. **View Logs**: `sudo journalctl -u ftth -f`
3. **Restart Services**: `sudo systemctl restart ftth`
4. **API Test**: `curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/health/"`

### If Yggdrasil Down
1. **Check Interface**: `ip addr show ygg0`
2. **Restart Yggdrasil**: `sudo systemctl restart yggdrasil`
3. **Test Connectivity**: `ping6 200:421e:6385:4a8b:dca7:cfb:197f:e9c3`
4. **API Test**: Verify all endpoints respond

### If Database Issues
1. **Check Connection**: Test database connectivity
2. **Verify Schema**: Check table structure matches models
3. **Backup Data**: Create emergency backup
4. **Restore Service**: Restart database service

---

## 🆕 New Features - January 2026

### Ingest Endpoints
- **Work Ingest**: `POST /works/ingest/work` - Import single work
- **Bulk Ingest**: `POST /works/ingest/bulk` - Import multiple works
- **Usage**: External systems can now push work data directly

### Equipment Tracking Enhancement
- **Modem Lifecycle**: Complete tracking from assignment to installation
- **ONT Lifecycle**: Full equipment management workflow
- **Delivery Tracking**: Separate delivery status from installation
- **Installation Notes**: Detailed technician documentation

### API Improvements
- **Unified Port**: All endpoints now on port 6030
- **Enhanced Security**: API key authentication for equipment endpoints
- **Better Error Handling**: Detailed error messages and status codes
- **Web Interface**: Direct access to HTML pages from root URLs