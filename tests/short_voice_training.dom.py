"""Built-app five-sample recognition UX with fake native ASR; blocks live API/cloud."""
import functools
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

root = Path(__file__).resolve().parents[1]
shop = '00000000-0000-0000-0000-000000000001'
key = 'street-ceo-pronunciation-v1'
posts = []


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root/'apps/web/dist')))
Thread(target=server.serve_forever, daemon=True).start()


def route(r):
    url = urlparse(r.request.url)
    if url.hostname == '127.0.0.1' and url.port == server.server_port:
        dist=(root/'apps/web/dist').resolve();asset=(dist/(url.path.lstrip('/') or 'index.html')).resolve()
        if asset.is_relative_to(dist) and asset.is_file():r.fulfill(path=str(asset))
        else:r.fulfill(status=404,body='Missing isolated fixture asset')
        return
    if url.hostname != 'shop.invalid':
        r.abort('blockedbyclient')
        return
    path = url.path
    if r.request.method == 'OPTIONS':
        r.fulfill(status=204, headers={'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': '*'})
        return
    if r.request.method == 'POST':
        posts.append(path)
    data = {'status': 'ready'} if path == '/readyz' else {'id': shop} if path == f'/shops/{shop}' else []
    r.fulfill(status=200, content_type='application/json', body=json.dumps(data), headers={'Access-Control-Allow-Origin': '*'})


try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True, timeout=20000, args=['--disable-gpu'])
        context = browser.new_context(viewport={'width': 390, 'height': 844},service_workers='block')
        context.route('**/*', route)
        context.add_init_script("""
        localStorage.setItem('street-ceo-api-config',JSON.stringify({baseUrl:'http://shop.invalid',shopId:'00000000-0000-0000-0000-000000000001'}));
        window.__listeners={};window.__prompts=[];window.__starts=0;
        window.__emit=(name,data={})=>{for(const fn of [...(window.__listeners[name]||[])])fn(data)};
        const plugin={async addListener(name,fn){(window.__listeners[name]??=new Set()).add(fn);return{async remove(){window.__listeners[name].delete(fn)}}},async start(){window.__starts++;setTimeout(()=>window.__emit('speechReady'),10)},async stop(){},async speak({text}){window.__prompts.push(text);await new Promise(resolve=>setTimeout(resolve,25))},async stopSpeaking(){}};
        window.Capacitor={getPlatform:()=> 'android',registerPlugin:()=>plugin};
        """)
        page = context.new_page()
        page.set_default_timeout(10000)
        page.goto(f'http://127.0.0.1:{server.server_port}', wait_until='domcontentloaded')
        page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Profile').click()
        setup = page.locator('.pronunciation-setup')
        expect(setup).to_be_visible()
        setup.get_by_role('button', name='Teach Napo').click()

        def capture(text, count):
            expect(setup.locator('.pronunciation-capture')).to_contain_text(f'Sample {count} of 5')
            page.wait_for_function("document.querySelector('.pronunciation-setup .voice-status')?.textContent.includes('Say Napo')")
            page.evaluate("text=>window.__emit('speech',{text,final:true})", text)
            page.evaluate("text=>window.__emit('speech',{text,final:true})", text)
            expect(setup.get_by_label('Phone heard')).to_have_value(text)

        # Cancelled drafts cannot partially save, even after a reviewed sample.
        capture('nepal', 1)
        setup.get_by_role('button', name='Keep sample').click()
        setup.get_by_role('button', name='Cancel', exact=True).click()
        assert page.evaluate('key=>localStorage.getItem(key)', key) is None
        setup.get_by_role('button', name='Teach Napo').click()
        samples = ['nepal', 'nepo', 'nopple', 'nepal', 'nah po']
        for i, text in enumerate(samples, 1):
            capture(text, i)
            assert page.evaluate('key=>localStorage.getItem(key)', key) is None
            if i == 5:
                page.evaluate("""() => {window.__setItem=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='street-ceo-pronunciation-v1')throw Error('Test storage unavailable');return window.__setItem.call(this,k,v)}}""")
                setup.get_by_role('button', name='Save all 5 samples').click()
                expect(setup.get_by_role('alert')).to_contain_text('Test storage unavailable')
                assert page.evaluate('key=>localStorage.getItem(key)', key) is None
                expect(setup.get_by_label('Phone heard')).to_have_value(text)
                page.evaluate('() => {Storage.prototype.setItem=window.__setItem}')
            setup.get_by_role('button', name='Save all 5 samples' if i == 5 else 'Keep sample').click()
        saved = json.loads(page.evaluate('key=>localStorage.getItem(key)', key))
        assert saved['napoAliases'] == ['nepal', 'nepo', 'nopple', 'nah po']
        expect(setup.locator('.pronunciation-saved')).to_contain_text('nepal, nepo, nopple, nah po')
        assert not posts, posts
        page.reload(wait_until='domcontentloaded')
        page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Profile').click()
        expect(setup.locator('.pronunciation-saved')).to_contain_text('nepal, nepo, nopple, nah po')
        page.evaluate("""() => {window.__removeItem=Storage.prototype.removeItem;Storage.prototype.removeItem=function(k){if(k==='street-ceo-pronunciation-v1')throw Error('Test reset blocked');return window.__removeItem.call(this,k)}}""")
        setup.get_by_role('button', name='Reset pronunciation', exact=True).click()
        expect(setup.get_by_role('alert')).to_contain_text('Could not reset')
        assert json.loads(page.evaluate('key=>localStorage.getItem(key)', key)) == saved
        page.evaluate('() => {Storage.prototype.removeItem=window.__removeItem}')
        setup.get_by_role('button', name='Reset pronunciation', exact=True).click()
        assert page.evaluate('key=>localStorage.getItem(key)', key) is None
        expect(setup.locator('.pronunciation-saved')).not_to_contain_text('nepal')
        assert not posts, posts
        print('DOM PASS: five reviewed fake-ASR samples, duplicate finals guarded, duplicates deduped, drafts Cancel no write, save/reset failure honesty, persisted reload, reset, zero API posts', flush=True)
        browser.close()
finally:
    server.shutdown()
    server.server_close()
