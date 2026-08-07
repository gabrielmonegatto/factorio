#!/bin/bash
# Factory Pulse — checks VPS containers, Teable tasks, and AgentMemory
# Called by the cron job. Results are injected into the agent's prompt.

VPS_IP="187.127.44.153"
SSH_KEY="~/.ssh/id_ed25519_factorio"
SSH_OPTS="-o ConnectTimeout=30 -o StrictHostKeyChecking=accept-new -i $SSH_KEY"

echo "=== CONTAINERS ==="
ssh $SSH_OPTS root@$VPS_IP "docker ps --format '{{.Names}}|{{.Status}}' && echo '---LOAD---' && uptime"

echo "=== TASKS ==="
ssh $SSH_OPTS root@$VPS_IP "docker exec factorio_teable_db psql -U teable -d teable -c \"SELECT Status, area, COUNT(*) FROM \\\"bseWeczeNfCSaMlu2EC\\\".\\\"tblVzN1Eo8tfk7GX2CJ\\\" GROUP BY Status, area ORDER BY COUNT(*) DESC;\""

echo "=== PENDING BY TASK ==="
ssh $SSH_OPTS root@$VPS_IP "docker exec factorio_teable_db psql -U teable -d teable -c \"SELECT task, COUNT(*) FROM \\\"bseWeczeNfCSaMlu2EC\\\".\\\"tblVzN1Eo8tfk7GX2CJ\\\" WHERE Status='Pendente' GROUP BY task ORDER BY COUNT(*) DESC;\""

echo "=== LAST MODIFIED ==="
ssh $SSH_OPTS root@$VPS_IP "docker exec factorio_teable_db psql -U teable -d teable -c \"SELECT MAX(\\\"__last_modified_time\\\") FROM \\\"bseWeczeNfCSaMlu2EC\\\".\\\"tblVzN1Eo8tfk7GX2CJ\\\";\""

echo "=== AGENTMEMORY HEALTH ==="
ssh $SSH_OPTS root@$VPS_IP "curl -s -o /dev/null -w '%{http_code}' http://localhost:3120/agentmemory/health -H 'Authorization: Bearer __AM_SECRET__'"

echo "=== AGENTMEMORY COUNT ==="
ssh $SSH_OPTS root@$VPS_IP "curl -s http://localhost:3120/agentmemory/memories -H 'Authorization: Bearer __AM_SECRET__' | python3 -c \"import json,sys; d=json.load(sys.stdin); print(f'Memories: {len(d.get(\\\"memories\\\",[]))}')\" 2>/dev/null || echo 'AM_FAILED'"