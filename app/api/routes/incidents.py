# """
# Mock ServiceNow incident data with Azure DevOps datafix links.

# ~40% of resolved incidents include a datafix_code snippet and an
# azure_devops_link pointing to the mock PR that fixed the issue.
# """

# import uuid
# from datetime import datetime, timedelta
# from typing import Any, Dict, List

# from fastapi import APIRouter, Query

# from app.schemas.incident import IncidentRecord, ReferenceField

# router = APIRouter()

# SERVICENOW_INSTANCE = "https://example.service-now.com"
# AZURE_DEVOPS_BASE = "https://dev.azure.com/example-org/ops-team/_git/datafixes/pullrequest"

# ASSIGNMENT_GROUPS = [
#     ("Network Operations",       "287ebd7da9fe198100f92cc8d1d2154e"),
#     ("Email Support",            "7f2a1c9e0b124af2a6e45018bcd401ab"),
#     ("Application Support",      "5b3d7d3c0f9c4ce196b4c16dbf0f3119"),
#     ("Desktop Support",          "0f61d3a12b5d48e7988fb9447f3e9ac2"),
#     ("Security Operations",      "31a22fb02f2e4e2e9653ceaa1c79d18f"),
#     ("Database Administration",  "a9c3b12e4f7d11e8a56f23bc9d04e871"),
#     ("Cloud Infrastructure",     "bc4d27f15a9e22f7b67031cd8e15f982"),
# ]

# GROUP_BY_NAME: Dict[str, tuple] = {
#     name: (name, gid) for name, gid in ASSIGNMENT_GROUPS
# }

# # ---------------------------------------------------------------------------
# # Incident templates.  Each entry may include an optional `datafix_code`
# # field.  When present, a mock Azure DevOps PR link is generated for that
# # incident at build time.
# # ---------------------------------------------------------------------------
# INCIDENT_TEMPLATES = [
#     {
#         "short_description": "VPN users unable to connect after password reset",
#         "description": (
#             "Remote users report VPN authentication failures after a mandatory "
#             "password reset. The Cisco AnyConnect client returns error Login "
#             "failed even with correct new credentials. Affects approximately "
#             "40 remote workers across all departments."
#         ),
#         "category": "network", "subcategory": "vpn",
#         "priority": "2 - High", "severity": "2 - Major",
#         "impact": "2 - Medium", "urgency": "1 - High",
#         "resolution_notes": (
#             "Root cause: RADIUS server cached old password hashes. Fix: flushed "
#             "RADIUS cache and restarted the authentication service. Users advised "
#             "to wait 10 minutes after password change before reconnecting VPN."
#         ),
#         "close_notes": "Resolved and confirmed with affected users.",
#         "group_key": "Network Operations",
#         "datafix_code": (
#             "#!/bin/bash\n"
#             "# Datafix: flush RADIUS cache and restart auth service\n"
#             "# Incident: VPN auth failures after password reset\n\n"
#             "echo 'Flushing RADIUS session cache...'\n"
#             "radclient -x localhost:1812 status secret\n"
#             "sudo systemctl stop freeradius\n"
#             "sudo rm -f /var/lib/radiusd/radutmp\n"
#             "sudo rm -f /var/lib/radiusd/radwtmp\n"
#             "sudo systemctl start freeradius\n"
#             "echo 'RADIUS cache flushed and service restarted.'\n"
#             "sudo systemctl status freeradius"
#         ),
#     },
#     {
#         "short_description": "External email delivery delayed over 30 minutes",
#         "description": (
#             "Users are receiving external email with delays greater than 30 "
#             "minutes. Internal email is unaffected. Exchange Online mail flow "
#             "dashboard shows a spike in queued messages. Marketing and Sales "
#             "teams report missed customer replies."
#         ),
#         "category": "software", "subcategory": "email",
#         "priority": "3 - Moderate", "severity": "3 - Minor",
#         "impact": "3 - Low", "urgency": "2 - Medium",
#         "resolution_notes": (
#             "MX record TTL had propagated incorrectly after a DNS migration. "
#             "Corrected MX record and cleared DNS caches on all mail relay nodes. "
#             "Mail flow normalised within 15 minutes of change."
#         ),
#         "close_notes": "Mail flow restored. No data loss.",
#         "group_key": "Email Support",
#         # No datafix — resolved via DNS config change, not code
#     },
#     {
#         "short_description": "Payroll application returns 500 error on login",
#         "description": (
#             "Employees see a 500 Internal Server Error when signing in to the "
#             "payroll portal. Error began at 08:00 UTC on payday. Approximately "
#             "600 employees cannot access pay slips. HR team reporting high call volume."
#         ),
#         "category": "application", "subcategory": "authentication",
#         "priority": "1 - Critical", "severity": "1 - Critical",
#         "impact": "1 - High", "urgency": "1 - High",
#         "resolution_notes": (
#             "Database connection pool exhausted due to a runaway reporting query "
#             "scheduled overnight. Query was killed, connection pool restarted, "
#             "and application recovered. Reporting job rescheduled to off-peak hours."
#         ),
#         "close_notes": "Portal restored. Payroll data intact.",
#         "group_key": "Application Support",
#         "datafix_code": (
#             "-- Datafix: kill runaway reporting query and reconfigure connection pool\n"
#             "-- Incident: Payroll app 500 errors due to DB pool exhaustion\n\n"
#             "-- Step 1: identify and kill the offending query\n"
#             "SELECT pid, now() - pg_stat_activity.query_start AS duration,\n"
#             "       query, state\n"
#             "FROM pg_stat_activity\n"
#             "WHERE state != 'idle' AND query_start < NOW() - INTERVAL '5 minutes'\n"
#             "ORDER BY duration DESC;\n\n"
#             "-- Kill the long-running query (replace <PID> with actual pid)\n"
#             "SELECT pg_terminate_backend(<PID>);\n\n"
#             "-- Step 2: increase connection pool size\n"
#             "ALTER SYSTEM SET max_connections = 200;\n"
#             "SELECT pg_reload_conf();\n\n"
#             "-- Step 3: verify pool is healthy\n"
#             "SELECT count(*) AS active_connections FROM pg_stat_activity\n"
#             "WHERE state != 'idle';"
#         ),
#     },
#     {
#         "short_description": "Laptop BitLocker recovery key prompted on every boot",
#         "description": (
#             "Corporate laptop repeatedly prompts for the BitLocker recovery key "
#             "on every boot after a Windows Update last night. User is a senior "
#             "analyst. Productivity fully blocked."
#         ),
#         "category": "hardware", "subcategory": "laptop",
#         "priority": "4 - Low", "severity": "3 - Minor",
#         "impact": "3 - Low", "urgency": "3 - Low",
#         "resolution_notes": (
#             "TPM PCR values changed after BIOS update included in the Windows "
#             "patch. Suspended BitLocker, applied patch, resumed protection. "
#             "Recovery key prompt no longer appears."
#         ),
#         "close_notes": "BitLocker functioning normally after BIOS patch.",
#         "group_key": "Desktop Support",
#         # No datafix — hardware/config fix
#     },
#     {
#         "short_description": "Knowledge base search returns empty results",
#         "description": (
#             "Customer portal knowledge base search returns zero results for "
#             "any query including known article titles. Elasticsearch index "
#             "health shows red status. Began after last night's maintenance window."
#         ),
#         "category": "application", "subcategory": "portal",
#         "priority": "2 - High", "severity": "2 - Major",
#         "impact": "2 - Medium", "urgency": "2 - Medium",
#         "resolution_notes": (
#             "Elasticsearch index mapping was lost during a snapshot restore. "
#             "Re-indexed all 12,000 knowledge articles from the source database. "
#             "Search operational within 45 minutes. Added index health monitoring alert."
#         ),
#         "close_notes": "Search restored. Monitoring alert configured.",
#         "group_key": "Application Support",
#         "datafix_code": (
#             "#!/usr/bin/env python3\n"
#             '"""Datafix: re-index knowledge articles after ES mapping loss."""\n'
#             "# Incident: KB search empty results after snapshot restore\n\n"
#             "from elasticsearch import Elasticsearch\n"
#             "import psycopg2, json\n\n"
#             "es = Elasticsearch('http://localhost:9200')\n"
#             "conn = psycopg2.connect('dbname=portal user=app')\n"
#             "cur = conn.cursor()\n\n"
#             "# Drop the broken index\n"
#             "if es.indices.exists(index='knowledge_articles'):\n"
#             "    es.indices.delete(index='knowledge_articles')\n"
#             "    print('Deleted corrupt index.')\n\n"
#             "# Recreate with correct mapping\n"
#             "mapping = {\n"
#             "    'mappings': {\n"
#             "        'properties': {\n"
#             "            'title': {'type': 'text'},\n"
#             "            'body':  {'type': 'text'},\n"
#             "            'tags':  {'type': 'keyword'},\n"
#             "        }\n"
#             "    }\n"
#             "}\n"
#             "es.indices.create(index='knowledge_articles', body=mapping)\n\n"
#             "# Bulk re-index from Postgres\n"
#             "cur.execute('SELECT id, title, body, tags FROM kb_articles')\n"
#             "rows = cur.fetchall()\n"
#             "for row in rows:\n"
#             "    es.index(index='knowledge_articles', id=row[0],\n"
#             "             document={'title': row[1], 'body': row[2], 'tags': row[3]})\n\n"
#             "print(f'Re-indexed {len(rows)} articles successfully.')\n"
#             "cur.close(); conn.close()"
#         ),
#     },
#     {
#         "short_description": "Third floor shared printer offline",
#         "description": (
#             "Users on the third floor cannot print to the shared HP LaserJet Pro. "
#             "Print jobs queue but never complete. Printer display shows Ready. "
#             "Rebooting the printer did not help."
#         ),
#         "category": "hardware", "subcategory": "printer",
#         "priority": "4 - Low", "severity": "4 - Low",
#         "impact": "3 - Low", "urgency": "3 - Low",
#         "resolution_notes": (
#             "Print spooler service had crashed on the print server. Restarted "
#             "spooler service and cleared the print queue. All queued jobs released."
#         ),
#         "close_notes": "Printer operational.",
#         "group_key": "Desktop Support",
#     },
#     {
#         "short_description": "Suspicious repeated failed sign-ins from unknown location",
#         "description": (
#             "Security monitoring detected 47 failed sign-in attempts for a user "
#             "account from a Tor exit node over 20 minutes. Account not yet locked. "
#             "User confirmed they are not travelling."
#         ),
#         "category": "security", "subcategory": "identity",
#         "priority": "2 - High", "severity": "2 - Major",
#         "impact": "2 - Medium", "urgency": "1 - High",
#         "resolution_notes": (
#             "Account locked, user notified, MFA reset completed, and conditional "
#             "access policy updated to block Tor exit nodes. No successful login "
#             "detected. SIEM alert tuned to auto-lock after 10 failures."
#         ),
#         "close_notes": "Account secured. Policy hardened.",
#         "group_key": "Security Operations",
#         "datafix_code": (
#             "# Datafix: block Tor exit nodes via Azure AD Conditional Access\n"
#             "# Incident: Brute-force from Tor exit node\n\n"
#             "from azure.identity import ClientSecretCredential\n"
#             "from msgraph.core import GraphClient\n\n"
#             "credential = ClientSecretCredential(\n"
#             "    tenant_id='<TENANT_ID>',\n"
#             "    client_id='<CLIENT_ID>',\n"
#             "    client_secret='<CLIENT_SECRET>',\n"
#             ")\n"
#             "client = GraphClient(credential=credential)\n\n"
#             "# Create named location for Tor exit nodes (update IP list regularly)\n"
#             "payload = {\n"
#             "    '@odata.type': '#microsoft.graph.ipNamedLocation',\n"
#             "    'displayName': 'Tor Exit Nodes - Blocked',\n"
#             "    'isTrusted': False,\n"
#             "    'ipRanges': [\n"
#             "        {'@odata.type': '#microsoft.graph.iPv4CidrRange', 'cidrAddress': '185.220.101.0/24'},\n"
#             "    ],\n"
#             "}\n"
#             "response = client.post('/identity/conditionalAccess/namedLocations', json=payload)\n"
#             "print('Named location created:', response.json()['id'])"
#         ),
#     },
#     {
#         "short_description": "Production database latency spike causing app timeouts",
#         "description": (
#             "Application response times spiked to over 10 seconds. Database "
#             "monitoring shows average query time increased from 20ms to 4000ms. "
#             "No schema changes deployed. Affects order processing and reporting."
#         ),
#         "category": "database", "subcategory": "performance",
#         "priority": "1 - Critical", "severity": "1 - Critical",
#         "impact": "1 - High", "urgency": "1 - High",
#         "resolution_notes": (
#             "Missing index on orders.customer_id detected after autovacuum ran "
#             "and table statistics were reset. Re-created index concurrently. "
#             "Query times returned to baseline within 5 minutes."
#         ),
#         "close_notes": "Performance restored. Index monitoring added.",
#         "group_key": "Database Administration",
#         "datafix_code": (
#             "-- Datafix: add missing index to restore query performance\n"
#             "-- Incident: DB latency spike due to missing index after autovacuum\n\n"
#             "-- Run CONCURRENTLY to avoid table lock on production\n"
#             "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_customer_id\n"
#             "    ON orders(customer_id);\n\n"
#             "-- Verify index is visible and healthy\n"
#             "SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read\n"
#             "FROM pg_stat_user_indexes\n"
#             "WHERE indexname = 'idx_orders_customer_id';\n\n"
#             "-- Update statistics immediately\n"
#             "ANALYZE orders;\n\n"
#             "-- Confirm query plan now uses the index\n"
#             "EXPLAIN ANALYZE\n"
#             "SELECT * FROM orders WHERE customer_id = 12345\n"
#             "LIMIT 10;"
#         ),
#     },
#     {
#         "short_description": "AWS EC2 instance unreachable after security group change",
#         "description": (
#             "Production web server became unreachable after a security group "
#             "rule was updated to restrict SSH. HTTP and HTTPS also stopped "
#             "responding. Change was made without peer review."
#         ),
#         "category": "cloud", "subcategory": "access",
#         "priority": "1 - Critical", "severity": "1 - Critical",
#         "impact": "1 - High", "urgency": "1 - High",
#         "resolution_notes": (
#             "Reverted security group to previous version via AWS console. Instance "
#             "became reachable immediately. Implemented change management policy "
#             "requiring peer approval for production security group modifications."
#         ),
#         "close_notes": "Instance restored. Change control policy updated.",
#         "group_key": "Cloud Infrastructure",
#         "datafix_code": (
#             "#!/usr/bin/env python3\n"
#             '"""Datafix: revert EC2 security group to last known good state."""\n'
#             "# Incident: EC2 unreachable after bad SG change\n\n"
#             "import boto3\n\n"
#             "ec2 = boto3.client('ec2', region_name='eu-west-1')\n"
#             "SG_ID = 'sg-0abc123def456789'\n\n"
#             "# Remove the bad rule that blocked all inbound traffic\n"
#             "ec2.revoke_security_group_ingress(\n"
#             "    GroupId=SG_ID,\n"
#             "    IpPermissions=[\n"
#             "        {'IpProtocol': '-1', 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},\n"
#             "    ],\n"
#             ")\n\n"
#             "# Restore correct rules\n"
#             "ec2.authorize_security_group_ingress(\n"
#             "    GroupId=SG_ID,\n"
#             "    IpPermissions=[\n"
#             "        {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443,\n"
#             "         'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTPS public'}]},\n"
#             "        {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22,\n"
#             "         'IpRanges': [{'CidrIp': '10.0.0.0/8', 'Description': 'SSH internal only'}]},\n"
#             "    ],\n"
#             ")\n"
#             "print(f'Security group {SG_ID} restored successfully.')"
#         ),
#     },
#     {
#         "short_description": "MFA authenticator app not generating valid codes",
#         "description": (
#             "Several users report the Microsoft Authenticator app is not "
#             "generating valid TOTP codes. Codes are always rejected at sign-in. "
#             "Affects users who recently got new phones. 15 users locked out."
#         ),
#         "category": "security", "subcategory": "mfa",
#         "priority": "2 - High", "severity": "2 - Major",
#         "impact": "2 - Medium", "urgency": "1 - High",
#         "resolution_notes": (
#             "Device clock drift of over 30 seconds on new phones caused TOTP "
#             "validation to fail. Instructed users to enable automatic time sync. "
#             "Re-enrolled MFA for all 15 affected accounts."
#         ),
#         "close_notes": "MFA re-enrolled for all affected users.",
#         "group_key": "Security Operations",
#     },
#     {
#         "short_description": "SharePoint document library sync errors on all Macs",
#         "description": (
#             "All macOS users report OneDrive for Business showing sync errors "
#             "for SharePoint document libraries. Windows users unaffected. "
#             "Error: Cannot connect to the server. Began after macOS 15.3 update."
#         ),
#         "category": "software", "subcategory": "collaboration",
#         "priority": "3 - Moderate", "severity": "3 - Minor",
#         "impact": "2 - Medium", "urgency": "2 - Medium",
#         "resolution_notes": (
#             "macOS 15.3 changed keychain access permissions for OneDrive tokens. "
#             "Workaround: re-authenticate OneDrive and grant full disk access. "
#             "Reported to Microsoft; patch expected in next release."
#         ),
#         "close_notes": "Workaround applied to all 87 Mac users.",
#         "group_key": "Desktop Support",
#     },
#     {
#         "short_description": "ERP system slow during month-end reporting",
#         "description": (
#             "SAP ERP is responding in 30-60 seconds for standard transactions "
#             "during month-end financial close. Normal response is under 3 seconds. "
#             "Finance team unable to complete period-end reports on schedule."
#         ),
#         "category": "application", "subcategory": "performance",
#         "priority": "2 - High", "severity": "2 - Major",
#         "impact": "1 - High", "urgency": "1 - High",
#         "resolution_notes": (
#             "Month-end batch jobs competing with online users for database I/O. "
#             "Rescheduled batch jobs to run between 22:00 and 06:00 UTC. "
#             "Added read replica for reporting queries to offload the primary DB."
#         ),
#         "close_notes": "Batch schedule updated. Read replica provisioned.",
#         "group_key": "Database Administration",
#         "datafix_code": (
#             "-- Datafix: reschedule competing month-end batch jobs\n"
#             "-- Incident: ERP slow due to batch/OLTP resource contention\n\n"
#             "-- Disable the conflicting daytime batch job\n"
#             "UPDATE batch_job_schedule\n"
#             "SET enabled = FALSE,\n"
#             "    schedule_cron = '0 22 * * *',   -- move to 22:00 UTC\n"
#             "    updated_at = NOW()\n"
#             "WHERE job_name IN ('month_end_gl_rollup', 'period_close_reporting')\n"
#             "  AND schedule_cron NOT LIKE '0 22%';\n\n"
#             "-- Redirect reporting queries to the read replica\n"
#             "UPDATE app_config\n"
#             "SET config_value = 'jdbc:postgresql://replica.db.internal:5432/erp'\n"
#             "WHERE config_key = 'REPORTING_DB_URL';\n\n"
#             "-- Verify change\n"
#             "SELECT job_name, schedule_cron, enabled FROM batch_job_schedule\n"
#             "WHERE job_name IN ('month_end_gl_rollup', 'period_close_reporting');"
#         ),
#     },
#     {
#         "short_description": "SSL certificate expired on customer API gateway",
#         "description": (
#             "External partners and customers receiving SSL handshake errors "
#             "calling the REST API at api.corp.com. Certificate expired today. "
#             "Alert was sent 30 days ago but renewal was not tracked. "
#             "Estimated 200 API calls per hour failing."
#         ),
#         "category": "network", "subcategory": "ssl",
#         "priority": "1 - Critical", "severity": "1 - Critical",
#         "impact": "1 - High", "urgency": "1 - High",
#         "resolution_notes": (
#             "Renewed certificate from DigiCert and deployed to all API gateway "
#             "nodes. Service restored in 12 minutes. Added certificate expiry "
#             "monitoring with 60-day and 30-day alerts to PagerDuty."
#         ),
#         "close_notes": "Certificate renewed. Monitoring added.",
#         "group_key": "Network Operations",
#         "datafix_code": (
#             "#!/bin/bash\n"
#             "# Datafix: emergency certificate renewal and deployment\n"
#             "# Incident: SSL cert expired on api.corp.com\n\n"
#             "DOMAIN='api.corp.com'\n"
#             "CERT_DIR='/etc/nginx/certs'\n\n"
#             "# Request new certificate from Let's Encrypt (or use your CA)\n"
#             "certbot certonly --webroot \\\n"
#             "  -w /var/www/html \\\n"
#             "  -d $DOMAIN \\\n"
#             "  --non-interactive \\\n"
#             "  --agree-tos \\\n"
#             "  --email ops@corp.com\n\n"
#             "# Copy to nginx cert directory\n"
#             "cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $CERT_DIR/$DOMAIN.crt\n"
#             "cp /etc/letsencrypt/live/$DOMAIN/privkey.pem   $CERT_DIR/$DOMAIN.key\n\n"
#             "# Reload nginx to pick up new cert without dropping connections\n"
#             "nginx -t && nginx -s reload\n\n"
#             "# Verify expiry\n"
#             "echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null \\\n"
#             "  | openssl x509 -noout -dates"
#         ),
#     },
#     {
#         "short_description": "CI/CD pipeline failing on all Python 3.12 builds",
#         "description": (
#             "All Jenkins pipeline jobs for Python services started failing after "
#             "the base image was updated to python:3.12-slim. "
#             "ImportError: cannot import name X from deprecated module. "
#             "18 microservices affected. Deployments blocked."
#         ),
#         "category": "application", "subcategory": "devops",
#         "priority": "2 - High", "severity": "2 - Major",
#         "impact": "2 - Medium", "urgency": "2 - Medium",
#         "resolution_notes": (
#             "Python 3.12 removed several deprecated stdlib modules used by "
#             "third-party packages. Pinned base image to python:3.11-slim and "
#             "opened tickets with package maintainers. Migration plan to 3.12 "
#             "scheduled for next sprint."
#         ),
#         "close_notes": "Pipeline unblocked. 3.12 migration planned.",
#         "group_key": "Cloud Infrastructure",
#         "datafix_code": (
#             "# Datafix: pin Python base image to 3.11 to unblock pipelines\n"
#             "# Incident: CI/CD failures after Python 3.12 base image update\n\n"
#             "# 1. Update Dockerfile in all affected services\n"
#             "import subprocess, pathlib\n\n"
#             "services_root = pathlib.Path('/workspace/services')\n"
#             "for dockerfile in services_root.rglob('Dockerfile'):\n"
#             "    text = dockerfile.read_text()\n"
#             "    if 'python:3.12' in text:\n"
#             "        dockerfile.write_text(text.replace('python:3.12-slim', 'python:3.11-slim'))\n"
#             "        print(f'Patched: {dockerfile}')\n\n"
#             "# 2. Commit and push\n"
#             "subprocess.run(['git', 'add', '-A'], cwd=services_root.parent)\n"
#             "subprocess.run(['git', 'commit', '-m',\n"
#             "                'fix: pin python base to 3.11-slim (INC0000014)'],\n"
#             "               cwd=services_root.parent)\n"
#             "subprocess.run(['git', 'push'], cwd=services_root.parent)\n"
#             "print('All Dockerfiles patched and pushed.')"
#         ),
#     },
#     {
#         "short_description": "Wi-Fi dropping on floor 2 near conference rooms",
#         "description": (
#             "Users on the second floor, particularly near the conference rooms, "
#             "report frequent Wi-Fi disconnections every 10-15 minutes. VoIP "
#             "calls dropping mid-meeting. Started after new LED lighting installed."
#         ),
#         "category": "network", "subcategory": "wireless",
#         "priority": "3 - Moderate", "severity": "3 - Minor",
#         "impact": "2 - Medium", "urgency": "2 - Medium",
#         "resolution_notes": (
#             "New LED driver units emitting RF interference on 2.4GHz band. "
#             "Changed affected access points to 5GHz only and adjusted channel "
#             "plans. Interference eliminated."
#         ),
#         "close_notes": "Wi-Fi stable after channel change.",
#         "group_key": "Network Operations",
#     },
# ]

# STATES = [
#     ("6 - Resolved", False),
#     ("6 - Resolved", False),
#     ("6 - Resolved", False),
#     ("2 - In Progress", True),
#     ("1 - New", True),
# ]


# def build_reference(table: str, sys_id: str) -> ReferenceField:
#     return ReferenceField(
#         link=f"{SERVICENOW_INSTANCE}/api/now/table/{table}/{sys_id}",
#         value=sys_id,
#     )


# def _make_date(days_ago: float, hour: int = 9, minute: int = 0) -> str:
#     dt = datetime.utcnow() - timedelta(days=days_ago)
#     return dt.replace(hour=hour, minute=minute, second=0, microsecond=0).strftime(
#         "%Y-%m-%d %H:%M:%S"
#     )


# def build_mock_incidents(total_records: int = 50) -> List[IncidentRecord]:
#     incidents: List[IncidentRecord] = []

#     for index in range(total_records):
#         template = INCIDENT_TEMPLATES[index % len(INCIDENT_TEMPLATES)]
#         state, active = STATES[index % len(STATES)]
#         sequence = index + 1

#         days_ago = 35.0 - (index * 35.0 / total_records)
#         opened_at   = _make_date(days_ago, hour=8 + (index % 10), minute=(index * 7) % 60)
#         created_on  = opened_at
#         updated_on  = _make_date(max(0.0, days_ago - 1), hour=10, minute=(index * 13) % 60)

#         group_key = template.get("group_key", ASSIGNMENT_GROUPS[index % len(ASSIGNMENT_GROUPS)][0])
#         group_name, group_id = GROUP_BY_NAME.get(
#             group_key, ASSIGNMENT_GROUPS[index % len(ASSIGNMENT_GROUPS)]
#         )

#         sys_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"mock-incident-{sequence}"))

#         servicenow_link = (
#             f"{SERVICENOW_INSTANCE}/nav_to.do"
#             f"?uri=incident.do%3Fsys_id%3D{sys_id.replace('-', '')}"
#         )

#         # Build Azure DevOps link only for resolved incidents that have a datafix
#         datafix_code = template.get("datafix_code", "")
#         azure_devops_link = ""
#         if datafix_code and not active:
#             pr_id = 1000 + sequence
#             azure_devops_link = f"{AZURE_DEVOPS_BASE}/{pr_id}"

#         incidents.append(
#             IncidentRecord(
#                 sys_id=sys_id,
#                 number=f"INC{sequence:07d}",
#                 short_description=template["short_description"],
#                 description=template["description"],
#                 category=template["category"],
#                 subcategory=template["subcategory"],
#                 priority=template["priority"],
#                 severity=template["severity"],
#                 state=state,
#                 incident_state=state,
#                 impact=template["impact"],
#                 urgency=template["urgency"],
#                 active=active,
#                 opened_at=opened_at,
#                 sys_created_on=created_on,
#                 sys_updated_on=updated_on,
#                 close_notes=template.get("close_notes", "") if not active else "",
#                 resolution_notes=template.get("resolution_notes", "") if not active else "",
#                 servicenow_link=servicenow_link,
#                 azure_devops_link=azure_devops_link,
#                 datafix_code=datafix_code if not active else "",
#                 assignment_group=build_reference("sys_user_group", group_id),
#                 assigned_to=build_reference(
#                     "sys_user", str(uuid.uuid5(uuid.NAMESPACE_DNS, f"user-{sequence}"))
#                 ),
#                 caller_id=build_reference(
#                     "sys_user", str(uuid.uuid5(uuid.NAMESPACE_DNS, f"caller-{sequence}"))
#                 ),
#                 cmdb_ci=build_reference(
#                     "cmdb_ci", str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ci-{sequence}"))
#                 ),
#             )
#         )

#     return incidents


# MOCK_INCIDENTS = build_mock_incidents()


# @router.get("/incidents", response_model=Dict[str, Any])
# def get_incidents(
#     limit: int = Query(default=10, ge=1),
#     offset: int = Query(default=0, ge=0),
# ):
#     total_records = len(MOCK_INCIDENTS)
#     paginated = MOCK_INCIDENTS[offset : offset + limit]
#     return {
#         "result": paginated,
#         "pagination": {
#             "total_records": total_records,
#             "returned_records": len(paginated),
#             "limit": limit,
#             "offset": offset,
#             "has_more": offset + len(paginated) < total_records,
#         },
#     }


"""
Mock ServiceNow incident data with Azure DevOps datafix links.

~40% of resolved incidents include a datafix_code snippet and an
azure_devops_link pointing to the mock PR that fixed the issue.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Query

from app.schemas.incident import IncidentRecord, ReferenceField

router = APIRouter()

SERVICENOW_INSTANCE = "https://example.service-now.com"
AZURE_DEVOPS_BASE = "https://dev.azure.com/example-org/ops-team/_git/datafixes/pullrequest"

ASSIGNMENT_GROUPS = [
    ("Network Operations",       "287ebd7da9fe198100f92cc8d1d2154e"),
    ("Email Support",            "7f2a1c9e0b124af2a6e45018bcd401ab"),
    ("Application Support",      "5b3d7d3c0f9c4ce196b4c16dbf0f3119"),
    ("Desktop Support",          "0f61d3a12b5d48e7988fb9447f3e9ac2"),
    ("Security Operations",      "31a22fb02f2e4e2e9653ceaa1c79d18f"),
    ("Database Administration",  "a9c3b12e4f7d11e8a56f23bc9d04e871"),
    ("Cloud Infrastructure",     "bc4d27f15a9e22f7b67031cd8e15f982"),
]

GROUP_BY_NAME: Dict[str, tuple] = {
    name: (name, gid) for name, gid in ASSIGNMENT_GROUPS
}

# ---------------------------------------------------------------------------
# Incident templates.  Each entry may include an optional `datafix_code`
# field.  When present, a mock Azure DevOps PR link is generated for that
# incident at build time.
# ---------------------------------------------------------------------------
INCIDENT_TEMPLATES = [
    {
        "short_description": "VPN users unable to connect after password reset",
        "description": (
            "Remote users report VPN authentication failures after a mandatory "
            "password reset. The Cisco AnyConnect client returns error Login "
            "failed even with correct new credentials. Affects approximately "
            "40 remote workers across all departments."
        ),
        "category": "network", "subcategory": "vpn",
        "priority": "2 - High", "severity": "2 - Major",
        "impact": "2 - Medium", "urgency": "1 - High",
        "resolution_notes": (
            "Root cause: RADIUS server cached old password hashes. Fix: flushed "
            "RADIUS cache and restarted the authentication service. Users advised "
            "to wait 10 minutes after password change before reconnecting VPN."
        ),
        "close_notes": "Resolved and confirmed with affected users.",
        "group_key": "Network Operations",
        "datafix_code": (
            "#!/bin/bash\n"
            "# Datafix: flush RADIUS cache and restart auth service\n"
            "# Incident: VPN auth failures after password reset\n\n"
            "echo 'Flushing RADIUS session cache...'\n"
            "radclient -x localhost:1812 status secret\n"
            "sudo systemctl stop freeradius\n"
            "sudo rm -f /var/lib/radiusd/radutmp\n"
            "sudo rm -f /var/lib/radiusd/radwtmp\n"
            "sudo systemctl start freeradius\n"
            "echo 'RADIUS cache flushed and service restarted.'\n"
            "sudo systemctl status freeradius"
        ),
    },
    {
        "short_description": "External email delivery delayed over 30 minutes",
        "description": (
            "Users are receiving external email with delays greater than 30 "
            "minutes. Internal email is unaffected. Exchange Online mail flow "
            "dashboard shows a spike in queued messages. Marketing and Sales "
            "teams report missed customer replies."
        ),
        "category": "software", "subcategory": "email",
        "priority": "3 - Moderate", "severity": "3 - Minor",
        "impact": "3 - Low", "urgency": "2 - Medium",
        "resolution_notes": (
            "MX record TTL had propagated incorrectly after a DNS migration. "
            "Corrected MX record and cleared DNS caches on all mail relay nodes. "
            "Mail flow normalised within 15 minutes of change."
        ),
        "close_notes": "Mail flow restored. No data loss.",
        "group_key": "Email Support",
        # No datafix — resolved via DNS config change, not code
    },
    {
        "short_description": "Payroll application returns 500 error on login",
        "description": (
            "Employees see a 500 Internal Server Error when signing in to the "
            "payroll portal. Error began at 08:00 UTC on payday. Approximately "
            "600 employees cannot access pay slips. HR team reporting high call volume."
        ),
        "category": "application", "subcategory": "authentication",
        "priority": "1 - Critical", "severity": "1 - Critical",
        "impact": "1 - High", "urgency": "1 - High",
        "resolution_notes": (
            "Database connection pool exhausted due to a runaway reporting query "
            "scheduled overnight. Query was killed, connection pool restarted, "
            "and application recovered. Reporting job rescheduled to off-peak hours."
        ),
        "close_notes": "Portal restored. Payroll data intact.",
        "group_key": "Application Support",
        "datafix_code": (
            "-- Datafix: kill runaway reporting query and reconfigure connection pool\n"
            "-- Incident: Payroll app 500 errors due to DB pool exhaustion\n\n"
            "-- Step 1: identify and kill the offending query\n"
            "SELECT pid, now() - pg_stat_activity.query_start AS duration,\n"
            "       query, state\n"
            "FROM pg_stat_activity\n"
            "WHERE state != 'idle' AND query_start < NOW() - INTERVAL '5 minutes'\n"
            "ORDER BY duration DESC;\n\n"
            "-- Kill the long-running query (replace <PID> with actual pid)\n"
            "SELECT pg_terminate_backend(<PID>);\n\n"
            "-- Step 2: increase connection pool size\n"
            "ALTER SYSTEM SET max_connections = 200;\n"
            "SELECT pg_reload_conf();\n\n"
            "-- Step 3: verify pool is healthy\n"
            "SELECT count(*) AS active_connections FROM pg_stat_activity\n"
            "WHERE state != 'idle';"
        ),
    },
    {
        "short_description": "Laptop BitLocker recovery key prompted on every boot",
        "description": (
            "Corporate laptop repeatedly prompts for the BitLocker recovery key "
            "on every boot after a Windows Update last night. User is a senior "
            "analyst. Productivity fully blocked."
        ),
        "category": "hardware", "subcategory": "laptop",
        "priority": "4 - Low", "severity": "3 - Minor",
        "impact": "3 - Low", "urgency": "3 - Low",
        "resolution_notes": (
            "TPM PCR values changed after BIOS update included in the Windows "
            "patch. Suspended BitLocker, applied patch, resumed protection. "
            "Recovery key prompt no longer appears."
        ),
        "close_notes": "BitLocker functioning normally after BIOS patch.",
        "group_key": "Desktop Support",
        # No datafix — hardware/config fix
    },
    {
        "short_description": "Knowledge base search returns empty results",
        "description": (
            "Customer portal knowledge base search returns zero results for "
            "any query including known article titles. Elasticsearch index "
            "health shows red status. Began after last night's maintenance window."
        ),
        "category": "application", "subcategory": "portal",
        "priority": "2 - High", "severity": "2 - Major",
        "impact": "2 - Medium", "urgency": "2 - Medium",
        "resolution_notes": (
            "Elasticsearch index mapping was lost during a snapshot restore. "
            "Re-indexed all 12,000 knowledge articles from the source database. "
            "Search operational within 45 minutes. Added index health monitoring alert."
        ),
        "close_notes": "Search restored. Monitoring alert configured.",
        "group_key": "Application Support",
        "datafix_code": (
            "#!/usr/bin/env python3\n"
            '"""Datafix: re-index knowledge articles after ES mapping loss."""\n'
            "# Incident: KB search empty results after snapshot restore\n\n"
            "from elasticsearch import Elasticsearch\n"
            "import psycopg2, json\n\n"
            "es = Elasticsearch('http://localhost:9200')\n"
            "conn = psycopg2.connect('dbname=portal user=app')\n"
            "cur = conn.cursor()\n\n"
            "# Drop the broken index\n"
            "if es.indices.exists(index='knowledge_articles'):\n"
            "    es.indices.delete(index='knowledge_articles')\n"
            "    print('Deleted corrupt index.')\n\n"
            "# Recreate with correct mapping\n"
            "mapping = {\n"
            "    'mappings': {\n"
            "        'properties': {\n"
            "            'title': {'type': 'text'},\n"
            "            'body':  {'type': 'text'},\n"
            "            'tags':  {'type': 'keyword'},\n"
            "        }\n"
            "    }\n"
            "}\n"
            "es.indices.create(index='knowledge_articles', body=mapping)\n\n"
            "# Bulk re-index from Postgres\n"
            "cur.execute('SELECT id, title, body, tags FROM kb_articles')\n"
            "rows = cur.fetchall()\n"
            "for row in rows:\n"
            "    es.index(index='knowledge_articles', id=row[0],\n"
            "             document={'title': row[1], 'body': row[2], 'tags': row[3]})\n\n"
            "print(f'Re-indexed {len(rows)} articles successfully.')\n"
            "cur.close(); conn.close()"
        ),
    },
    {
        "short_description": "Third floor shared printer offline",
        "description": (
            "Users on the third floor cannot print to the shared HP LaserJet Pro. "
            "Print jobs queue but never complete. Printer display shows Ready. "
            "Rebooting the printer did not help."
        ),
        "category": "hardware", "subcategory": "printer",
        "priority": "4 - Low", "severity": "4 - Low",
        "impact": "3 - Low", "urgency": "3 - Low",
        "resolution_notes": (
            "Print spooler service had crashed on the print server. Restarted "
            "spooler service and cleared the print queue. All queued jobs released."
        ),
        "close_notes": "Printer operational.",
        "group_key": "Desktop Support",
    },
    {
        "short_description": "Suspicious repeated failed sign-ins from unknown location",
        "description": (
            "Security monitoring detected 47 failed sign-in attempts for a user "
            "account from a Tor exit node over 20 minutes. Account not yet locked. "
            "User confirmed they are not travelling."
        ),
        "category": "security", "subcategory": "identity",
        "priority": "2 - High", "severity": "2 - Major",
        "impact": "2 - Medium", "urgency": "1 - High",
        "resolution_notes": (
            "Account locked, user notified, MFA reset completed, and conditional "
            "access policy updated to block Tor exit nodes. No successful login "
            "detected. SIEM alert tuned to auto-lock after 10 failures."
        ),
        "close_notes": "Account secured. Policy hardened.",
        "group_key": "Security Operations",
        "datafix_code": (
            "# Datafix: block Tor exit nodes via Azure AD Conditional Access\n"
            "# Incident: Brute-force from Tor exit node\n\n"
            "from azure.identity import ClientSecretCredential\n"
            "from msgraph.core import GraphClient\n\n"
            "credential = ClientSecretCredential(\n"
            "    tenant_id='<TENANT_ID>',\n"
            "    client_id='<CLIENT_ID>',\n"
            "    client_secret='<CLIENT_SECRET>',\n"
            ")\n"
            "client = GraphClient(credential=credential)\n\n"
            "# Create named location for Tor exit nodes (update IP list regularly)\n"
            "payload = {\n"
            "    '@odata.type': '#microsoft.graph.ipNamedLocation',\n"
            "    'displayName': 'Tor Exit Nodes - Blocked',\n"
            "    'isTrusted': False,\n"
            "    'ipRanges': [\n"
            "        {'@odata.type': '#microsoft.graph.iPv4CidrRange', 'cidrAddress': '185.220.101.0/24'},\n"
            "    ],\n"
            "}\n"
            "response = client.post('/identity/conditionalAccess/namedLocations', json=payload)\n"
            "print('Named location created:', response.json()['id'])"
        ),
    },
    {
        "short_description": "Production database latency spike causing app timeouts",
        "description": (
            "Application response times spiked to over 10 seconds. Database "
            "monitoring shows average query time increased from 20ms to 4000ms. "
            "No schema changes deployed. Affects order processing and reporting."
        ),
        "category": "database", "subcategory": "performance",
        "priority": "1 - Critical", "severity": "1 - Critical",
        "impact": "1 - High", "urgency": "1 - High",
        "resolution_notes": (
            "Missing index on orders.customer_id detected after autovacuum ran "
            "and table statistics were reset. Re-created index concurrently. "
            "Query times returned to baseline within 5 minutes."
        ),
        "close_notes": "Performance restored. Index monitoring added.",
        "group_key": "Database Administration",
        "datafix_code": (
            "-- Datafix: add missing index to restore query performance\n"
            "-- Incident: DB latency spike due to missing index after autovacuum\n\n"
            "-- Run CONCURRENTLY to avoid table lock on production\n"
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_customer_id\n"
            "    ON orders(customer_id);\n\n"
            "-- Verify index is visible and healthy\n"
            "SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read\n"
            "FROM pg_stat_user_indexes\n"
            "WHERE indexname = 'idx_orders_customer_id';\n\n"
            "-- Update statistics immediately\n"
            "ANALYZE orders;\n\n"
            "-- Confirm query plan now uses the index\n"
            "EXPLAIN ANALYZE\n"
            "SELECT * FROM orders WHERE customer_id = 12345\n"
            "LIMIT 10;"
        ),
    },
    {
        "short_description": "AWS EC2 instance unreachable after security group change",
        "description": (
            "Production web server became unreachable after a security group "
            "rule was updated to restrict SSH. HTTP and HTTPS also stopped "
            "responding. Change was made without peer review."
        ),
        "category": "cloud", "subcategory": "access",
        "priority": "1 - Critical", "severity": "1 - Critical",
        "impact": "1 - High", "urgency": "1 - High",
        "resolution_notes": (
            "Reverted security group to previous version via AWS console. Instance "
            "became reachable immediately. Implemented change management policy "
            "requiring peer approval for production security group modifications."
        ),
        "close_notes": "Instance restored. Change control policy updated.",
        "group_key": "Cloud Infrastructure",
        "datafix_code": (
            "#!/usr/bin/env python3\n"
            '"""Datafix: revert EC2 security group to last known good state."""\n'
            "# Incident: EC2 unreachable after bad SG change\n\n"
            "import boto3\n\n"
            "ec2 = boto3.client('ec2', region_name='eu-west-1')\n"
            "SG_ID = 'sg-0abc123def456789'\n\n"
            "# Remove the bad rule that blocked all inbound traffic\n"
            "ec2.revoke_security_group_ingress(\n"
            "    GroupId=SG_ID,\n"
            "    IpPermissions=[\n"
            "        {'IpProtocol': '-1', 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},\n"
            "    ],\n"
            ")\n\n"
            "# Restore correct rules\n"
            "ec2.authorize_security_group_ingress(\n"
            "    GroupId=SG_ID,\n"
            "    IpPermissions=[\n"
            "        {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443,\n"
            "         'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTPS public'}]},\n"
            "        {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22,\n"
            "         'IpRanges': [{'CidrIp': '10.0.0.0/8', 'Description': 'SSH internal only'}]},\n"
            "    ],\n"
            ")\n"
            "print(f'Security group {SG_ID} restored successfully.')"
        ),
    },
    {
        "short_description": "MFA authenticator app not generating valid codes",
        "description": (
            "Several users report the Microsoft Authenticator app is not "
            "generating valid TOTP codes. Codes are always rejected at sign-in. "
            "Affects users who recently got new phones. 15 users locked out."
        ),
        "category": "security", "subcategory": "mfa",
        "priority": "2 - High", "severity": "2 - Major",
        "impact": "2 - Medium", "urgency": "1 - High",
        "resolution_notes": (
            "Device clock drift of over 30 seconds on new phones caused TOTP "
            "validation to fail. Instructed users to enable automatic time sync. "
            "Re-enrolled MFA for all 15 affected accounts."
        ),
        "close_notes": "MFA re-enrolled for all affected users.",
        "group_key": "Security Operations",
    },
    {
        "short_description": "SharePoint document library sync errors on all Macs",
        "description": (
            "All macOS users report OneDrive for Business showing sync errors "
            "for SharePoint document libraries. Windows users unaffected. "
            "Error: Cannot connect to the server. Began after macOS 15.3 update."
        ),
        "category": "software", "subcategory": "collaboration",
        "priority": "3 - Moderate", "severity": "3 - Minor",
        "impact": "2 - Medium", "urgency": "2 - Medium",
        "resolution_notes": (
            "macOS 15.3 changed keychain access permissions for OneDrive tokens. "
            "Workaround: re-authenticate OneDrive and grant full disk access. "
            "Reported to Microsoft; patch expected in next release."
        ),
        "close_notes": "Workaround applied to all 87 Mac users.",
        "group_key": "Desktop Support",
    },
    {
        "short_description": "ERP system slow during month-end reporting",
        "description": (
            "SAP ERP is responding in 30-60 seconds for standard transactions "
            "during month-end financial close. Normal response is under 3 seconds. "
            "Finance team unable to complete period-end reports on schedule."
        ),
        "category": "application", "subcategory": "performance",
        "priority": "2 - High", "severity": "2 - Major",
        "impact": "1 - High", "urgency": "1 - High",
        "resolution_notes": (
            "Month-end batch jobs competing with online users for database I/O. "
            "Rescheduled batch jobs to run between 22:00 and 06:00 UTC. "
            "Added read replica for reporting queries to offload the primary DB."
        ),
        "close_notes": "Batch schedule updated. Read replica provisioned.",
        "group_key": "Database Administration",
        "datafix_code": (
            "-- Datafix: reschedule competing month-end batch jobs\n"
            "-- Incident: ERP slow due to batch/OLTP resource contention\n\n"
            "-- Disable the conflicting daytime batch job\n"
            "UPDATE batch_job_schedule\n"
            "SET enabled = FALSE,\n"
            "    schedule_cron = '0 22 * * *',   -- move to 22:00 UTC\n"
            "    updated_at = NOW()\n"
            "WHERE job_name IN ('month_end_gl_rollup', 'period_close_reporting')\n"
            "  AND schedule_cron NOT LIKE '0 22%';\n\n"
            "-- Redirect reporting queries to the read replica\n"
            "UPDATE app_config\n"
            "SET config_value = 'jdbc:postgresql://replica.db.internal:5432/erp'\n"
            "WHERE config_key = 'REPORTING_DB_URL';\n\n"
            "-- Verify change\n"
            "SELECT job_name, schedule_cron, enabled FROM batch_job_schedule\n"
            "WHERE job_name IN ('month_end_gl_rollup', 'period_close_reporting');"
        ),
    },
    {
        "short_description": "SSL certificate expired on customer API gateway",
        "description": (
            "External partners and customers receiving SSL handshake errors "
            "calling the REST API at api.corp.com. Certificate expired today. "
            "Alert was sent 30 days ago but renewal was not tracked. "
            "Estimated 200 API calls per hour failing."
        ),
        "category": "network", "subcategory": "ssl",
        "priority": "1 - Critical", "severity": "1 - Critical",
        "impact": "1 - High", "urgency": "1 - High",
        "resolution_notes": (
            "Renewed certificate from DigiCert and deployed to all API gateway "
            "nodes. Service restored in 12 minutes. Added certificate expiry "
            "monitoring with 60-day and 30-day alerts to PagerDuty."
        ),
        "close_notes": "Certificate renewed. Monitoring added.",
        "group_key": "Network Operations",
        "datafix_code": (
            "#!/bin/bash\n"
            "# Datafix: emergency certificate renewal and deployment\n"
            "# Incident: SSL cert expired on api.corp.com\n\n"
            "DOMAIN='api.corp.com'\n"
            "CERT_DIR='/etc/nginx/certs'\n\n"
            "# Request new certificate from Let's Encrypt (or use your CA)\n"
            "certbot certonly --webroot \\\n"
            "  -w /var/www/html \\\n"
            "  -d $DOMAIN \\\n"
            "  --non-interactive \\\n"
            "  --agree-tos \\\n"
            "  --email ops@corp.com\n\n"
            "# Copy to nginx cert directory\n"
            "cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $CERT_DIR/$DOMAIN.crt\n"
            "cp /etc/letsencrypt/live/$DOMAIN/privkey.pem   $CERT_DIR/$DOMAIN.key\n\n"
            "# Reload nginx to pick up new cert without dropping connections\n"
            "nginx -t && nginx -s reload\n\n"
            "# Verify expiry\n"
            "echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null \\\n"
            "  | openssl x509 -noout -dates"
        ),
    },
    {
        "short_description": "CI/CD pipeline failing on all Python 3.12 builds",
        "description": (
            "All Jenkins pipeline jobs for Python services started failing after "
            "the base image was updated to python:3.12-slim. "
            "ImportError: cannot import name X from deprecated module. "
            "18 microservices affected. Deployments blocked."
        ),
        "category": "application", "subcategory": "devops",
        "priority": "2 - High", "severity": "2 - Major",
        "impact": "2 - Medium", "urgency": "2 - Medium",
        "resolution_notes": (
            "Python 3.12 removed several deprecated stdlib modules used by "
            "third-party packages. Pinned base image to python:3.11-slim and "
            "opened tickets with package maintainers. Migration plan to 3.12 "
            "scheduled for next sprint."
        ),
        "close_notes": "Pipeline unblocked. 3.12 migration planned.",
        "group_key": "Cloud Infrastructure",
        "datafix_code": (
            "# Datafix: pin Python base image to 3.11 to unblock pipelines\n"
            "# Incident: CI/CD failures after Python 3.12 base image update\n\n"
            "# 1. Update Dockerfile in all affected services\n"
            "import subprocess, pathlib\n\n"
            "services_root = pathlib.Path('/workspace/services')\n"
            "for dockerfile in services_root.rglob('Dockerfile'):\n"
            "    text = dockerfile.read_text()\n"
            "    if 'python:3.12' in text:\n"
            "        dockerfile.write_text(text.replace('python:3.12-slim', 'python:3.11-slim'))\n"
            "        print(f'Patched: {dockerfile}')\n\n"
            "# 2. Commit and push\n"
            "subprocess.run(['git', 'add', '-A'], cwd=services_root.parent)\n"
            "subprocess.run(['git', 'commit', '-m',\n"
            "                'fix: pin python base to 3.11-slim (INC0000014)'],\n"
            "               cwd=services_root.parent)\n"
            "subprocess.run(['git', 'push'], cwd=services_root.parent)\n"
            "print('All Dockerfiles patched and pushed.')"
        ),
    },
    {
        "short_description": "Wi-Fi dropping on floor 2 near conference rooms",
        "description": (
            "Users on the second floor, particularly near the conference rooms, "
            "report frequent Wi-Fi disconnections every 10-15 minutes. VoIP "
            "calls dropping mid-meeting. Started after new LED lighting installed."
        ),
        "category": "network", "subcategory": "wireless",
        "priority": "3 - Moderate", "severity": "3 - Minor",
        "impact": "2 - Medium", "urgency": "2 - Medium",
        "resolution_notes": (
            "New LED driver units emitting RF interference on 2.4GHz band. "
            "Changed affected access points to 5GHz only and adjusted channel "
            "plans. Interference eliminated."
        ),
        "close_notes": "Wi-Fi stable after channel change.",
        "group_key": "Network Operations",
    },
]

STATES = [
    ("6 - Resolved", False),
    ("6 - Resolved", False),
    ("6 - Resolved", False),
    ("2 - In Progress", True),
    ("1 - New", True),
]


def build_reference(table: str, sys_id: str) -> ReferenceField:
    return ReferenceField(
        link=f"{SERVICENOW_INSTANCE}/api/now/table/{table}/{sys_id}",
        value=sys_id,
    )


def _make_date(days_ago: float, hour: int = 9, minute: int = 0) -> str:
    # Fixed Bug: datetime.utcnow() deprecation in Python 3.12 replaced with timezone.utc
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.replace(hour=hour, minute=minute, second=0, microsecond=0).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def build_mock_incidents(total_records: int = 50) -> List[IncidentRecord]:
    incidents: List[IncidentRecord] = []

    for index in range(total_records):
        template = INCIDENT_TEMPLATES[index % len(INCIDENT_TEMPLATES)]
        state, active = STATES[index % len(STATES)]
        sequence = index + 1

        days_ago = 35.0 - (index * 35.0 / total_records)
        opened_at   = _make_date(days_ago, hour=8 + (index % 10), minute=(index * 7) % 60)
        created_on  = opened_at
        updated_on  = _make_date(max(0.0, days_ago - 1), hour=10, minute=(index * 13) % 60)

        group_key = template.get("group_key", ASSIGNMENT_GROUPS[index % len(ASSIGNMENT_GROUPS)][0])
        group_name, group_id = GROUP_BY_NAME.get(
            group_key, ASSIGNMENT_GROUPS[index % len(ASSIGNMENT_GROUPS)]
        )

        sys_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"mock-incident-{sequence}"))

        servicenow_link = (
            f"{SERVICENOW_INSTANCE}/nav_to.do"
            f"?uri=incident.do%3Fsys_id%3D{sys_id.replace('-', '')}"
        )

        # Build Azure DevOps link only for resolved incidents that have a datafix
        datafix_code = template.get("datafix_code", "")
        azure_devops_link = ""
        if datafix_code and not active:
            pr_id = 1000 + sequence
            azure_devops_link = f"{AZURE_DEVOPS_BASE}/{pr_id}"

        incidents.append(
            IncidentRecord(
                sys_id=sys_id,
                number=f"INC{sequence:07d}",
                short_description=template["short_description"],
                description=template["description"],
                category=template["category"],
                subcategory=template["subcategory"],
                priority=template["priority"],
                severity=template["severity"],
                state=state,
                incident_state=state,
                impact=template["impact"],
                urgency=template["urgency"],
                active=active,
                opened_at=opened_at,
                sys_created_on=created_on,
                sys_updated_on=updated_on,
                close_notes=template.get("close_notes", "") if not active else "",
                resolution_notes=template.get("resolution_notes", "") if not active else "",
                servicenow_link=servicenow_link,
                azure_devops_link=azure_devops_link,
                datafix_code=datafix_code if not active else "",
                assignment_group=build_reference("sys_user_group", group_id),
                assigned_to=build_reference(
                    "sys_user", str(uuid.uuid5(uuid.NAMESPACE_DNS, f"user-{sequence}"))
                ),
                caller_id=build_reference(
                    "sys_user", str(uuid.uuid5(uuid.NAMESPACE_DNS, f"caller-{sequence}"))
                ),
                cmdb_ci=build_reference(
                    "cmdb_ci", str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ci-{sequence}"))
                ),
            )
        )

    return incidents


MOCK_INCIDENTS = build_mock_incidents()


@router.get("/incidents", response_model=Dict[str, Any])
def get_incidents(
    limit: int = Query(default=10, ge=1),
    offset: int = Query(default=0, ge=0),
):
    total_records = len(MOCK_INCIDENTS)
    paginated = MOCK_INCIDENTS[offset : offset + limit]
    return {
        "result": paginated,
        "pagination": {
            "total_records": total_records,
            "returned_records": len(paginated),
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(paginated) < total_records,
        },
    }