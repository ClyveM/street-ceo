import assert from 'node:assert/strict'
import {test} from 'node:test'
import {readFile} from 'node:fs/promises'
import vm from 'node:vm'
const source=await readFile(new URL('../public/service-worker.js',import.meta.url),'utf8')
function worker(){
 const handlers={},calls=[]
 const context={
  URL,
  self:{location:{origin:'http://localhost'},addEventListener(name,callback){handlers[name]=callback}},
  fetch(){calls.push('fetch');return Promise.reject(Error('offline'))},
  caches:{open(){calls.push('cache open');return Promise.resolve({put(){calls.push('put')}})},match(){calls.push('cache match');return Promise.resolve('HTML shell')}},
 }
 vm.runInNewContext(source,context)
 return{handlers,calls}
}
test('service worker leaves API, cross-origin and no-store probes network-only without cache or HTML fallback',()=>{
 for(const [path,cache] of [['/readyz','default'],['/healthz','default'],['/shops/shop-1','default'],['/api/v1/demo/runtime','default'],['/api/v1/shops/shop-1/sales','default'],['http://192.168.10.213:8001/readyz','default'],['/any-probe','no-store']]){
  const {handlers,calls}=worker();let intercepted=false
  handlers.fetch({request:{url:new URL(path,'http://localhost').href,method:'GET',cache},respondWith(){intercepted=true}})
  assert.equal(intercepted,false,path);assert.deepEqual(calls,[],path)
 }
})
test('shell navigation retains its existing fallback separately from API traffic',async()=>{
 const {handlers,calls}=worker();let response
 handlers.fetch({request:{url:'http://localhost/index.html',method:'GET',cache:'default'},respondWith(promise){response=promise}})
 assert.equal(await response,'HTML shell');assert.ok(calls.includes('fetch'));assert.ok(calls.includes('cache match'))
})
