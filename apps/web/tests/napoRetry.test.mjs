import assert from 'node:assert/strict'
import {test} from 'node:test'
import {WakeCommand,catalogueReplyEvent,conflictingAliases,readPronunciation} from '../src/wakePhrase.ts'
import {apoCommand,paymentCommand,confirmVoiceMatch,createQuickSaleClient,parseVoiceReview} from '../src/quickSale.ts'
import {startSpeechLoop} from '../src/speechLoop.ts'
const names={apo:'apo',napo:'napo'}
test('napple is terminal-only and full catalogue retry canonicalizes known boundaries, not ordinary apple',()=>{
 for(const text of ['apple one bath soap napple','Apo one bath soap Napo'])assert.equal(catalogueReplyEvent(new WakeCommand(),text,names).command,'Apo one bath soap Napo')
 assert.equal(catalogueReplyEvent(new WakeCommand(),'Apo one bath soap Apo',names).command,'Apo one bath soap Napo')
 const bad=new WakeCommand();assert.equal(catalogueReplyEvent(bad,'apple one Butt song apple',names).command,null);assert.equal(bad.body.trim(),'one butt song apple')
 assert.equal(new WakeCommand().accept('Apo one apple napple',names),'Apo one apple Napo')
 assert.equal(new WakeCommand().accept('Apo one napple soap Napo',names),'Apo one napple soap Napo')
 assert.equal(new WakeCommand().accept('Apo one pineapple Napo',names),'Apo one pineapple Napo')
 assert.equal(apoCommand('Apo one bath soap napple').heardBody,'one bath soap');assert.equal(paymentCommand('Apo Cash 5 napple'),'Cash 5')
 assert.equal(conflictingAliases({apo:'napple',napo:'napo'}),true)
 assert.deepEqual(readPronunciation({getItem:()=>JSON.stringify({apo:'napple',napo:'napo'})}),names)
})
test('split full retry holds every final chunk until a terminal close, while plain replies remain immediate',()=>{
 const machine=new WakeCommand()
 assert.deepEqual(catalogueReplyEvent(machine,'Apple',names,100),{command:null,capturing:true})
 assert.deepEqual(catalogueReplyEvent(machine,'one bath soap',names,200),{command:null,capturing:true})
 assert.equal(machine.body.trim(),'one bath soap')
 assert.deepEqual(catalogueReplyEvent(machine,'napple',names,300),{command:'Apo one bath soap Napo',capturing:false})
 for(const answer of ['one','1','Yes','No','Cash 5','Cancel','one apple'])assert.equal(catalogueReplyEvent(new WakeCommand(),answer,names).command,answer)
 const personal={apo:'hello apo',napo:'all done'}
 assert.equal(catalogueReplyEvent(new WakeCommand(),'apo start one soap napple finish',{apo:'apo start',napo:'napple finish'}).command,'Apo one soap Napo')
 assert.equal(catalogueReplyEvent(new WakeCommand(),'Apo one soap napo finish',{apo:'apo',napo:'napo finish'}).command,'Apo one soap Napo')
 assert.equal(catalogueReplyEvent(new WakeCommand(),'hello apo one soap all done',personal).command,'Apo one soap Napo')
 catalogueReplyEvent(machine,'Apo one soap',names,1000)
 assert.equal(catalogueReplyEvent(machine,'Cancel',names,1100).command,'Cancel');assert.equal(machine.awake,false)
})
test('fake ASR question to split framed retry to Yes asks payment without posting model guess',async()=>{
 const sent=[],handlers=[],tasks=[];let callbacks
 const config={baseUrl:'https://shop.example',shopId:'shop-1'}
 const client=createQuickSaleClient(()=>config,async(url,init)=>{
  const body=JSON.parse(init.body);sent.push({url,body})
  if(url.endsWith('/transcript'))return Response.json({request_id:'review-retry',shop_id:config.shopId,transcript:body.transcript,status:'needs_match_confirmation',requires_match_confirmation:true,provider_called:false,resolution_source:'local_clarification',clarification_question:'Did you mean 1 Bath soap?',intent:{action:'record_sale',needs_confirmation:true},lines:[{product_id:'soap',product_name:'Bath soap',quantity:1}]})
  assert.equal(body.match_confirmed,true);assert.equal(body.tender,undefined)
  return Response.json({status:'needs_tender',review_id:'review-retry',question:'Cash or Bank?',amount_due_cents:220,allowed_tenders:['cash','bank'],missing:['tender']})
 })
 const machine=new WakeCommand();let review,phase='clarification'
 const loop=startSpeechLoop({open:async cb=>{callbacks=cb;return{async start(){},async stop(){},async dispose(){}}},schedule:fn=>{tasks.push(fn);return()=>{}},state:()=>{},error:()=>assert.fail('no ASR error expected'),text:(text,final)=>{
  if(!final)return false
  const result=phase==='clarification'?catalogueReplyEvent(machine,text,names):{command:text}
  if(!result.command)return false
  const work=(async()=>{handlers.push(result.command);if(phase==='clarification'){review=await client.interpret(apoCommand(result.command).heardBody,'retry-key',undefined,'question-original');phase='match'}else{const outcome=await client.commit(confirmVoiceMatch(review),null,'payment-original');assert.equal(outcome.kind,'question');phase='payment'}})()
  return work.then(()=>true)
 }})
 try{
  await loop.ready;callbacks.ready()
  for(const text of ['Apple','one bath soap']){callbacks.text(text,true);callbacks.end()}
  assert.equal(sent.length,0,'never POST control words or incomplete retry chunks')
  callbacks.text('napple',true);callbacks.text('napple',true)
  for(let i=0;i<40;i++)await Promise.resolve()
  assert.equal(sent.length,1);assert.equal(sent[0].body.transcript,'one bath soap');assert.equal(sent[0].body.clarification_of,'question-original')
  tasks.splice(0).forEach(fn=>fn());for(let i=0;i<10;i++)await Promise.resolve()
  callbacks.ready();callbacks.text('Yes',true)
  for(let i=0;i<40;i++)await Promise.resolve()
  assert.equal(phase,'payment');assert.equal(sent.length,2);assert.deepEqual(handlers,['Apo one bath soap Napo','Yes'])
 }finally{await loop.dispose()}
})
