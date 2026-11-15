# De Touch – Telegram relay: every 5 minutes, fetch queued notifications from the company system and send them.
import json, os, sys, urllib.request

API = os.environ.get('TG_API', 'https://api.telegram.org')
TOKEN, APP, KEY = os.environ.get('TG_TOKEN', ''), os.environ.get('APP_URL', ''), os.environ.get('RELAY_KEY', '')
if not (TOKEN and APP and KEY):
    sys.exit('Missing secrets: TG_TOKEN, APP_URL, RELAY_KEY')

def post(url, data, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())

def app(data):
    r = post(APP, dict(data, relay=KEY))
    if not r.get('ok'):
        sys.exit('System error: ' + str(r.get('error')))
    return r['result']

def tg(method, data):
    try:
        return post('%s/bot%s/%s' % (API, TOKEN, method), data, 30)
    except Exception as e:
        print('telegram error', method, e)
        return {}

state = app({'op': 'state'})
ups = tg('getUpdates', {'offset': state['offset'], 'timeout': 0, 'allowed_updates': ['message']}).get('result', [])
res = app({'op': 'tick', 'updates': ups})
sent = 0
for m in res.get('msgs', []):
    p = {'chat_id': m['chat'], 'text': m['text'], 'parse_mode': 'HTML', 'disable_web_page_preview': True}
    if m.get('btn') and res.get('url'):
        p['reply_markup'] = {'inline_keyboard': [[{'text': m['btn'], 'url': res['url']}]]}
    if tg('sendMessage', p).get('ok'):
        sent += 1
print('updates: %d · messages: %d/%d' % (len(ups), sent, len(res.get('msgs', []))))
