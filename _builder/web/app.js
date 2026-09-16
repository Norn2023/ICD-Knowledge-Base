var D=null,CC={'手术':'#d4e6ff','诊断性操作':'#e0f0e0','治疗性操作':'#fff3d4','介入治疗':'#fde0e0'},CL={'手术':'🔪','诊断性操作':'🔬','治疗性操作':'💊','介入治疗':'🩻'};
var _dl=document.getElementById('load');
function _rdy(){_dl.style.display='none';document.querySelector('main').style.display='block';s10();s9();sd()}
fetch('data.json').then(function(r){return r.json()}).then(function(d){
D=d;D.m10={};d.icd10.forEach(function(c){D.m10[c.c]=c});D.m9={};d.icd9.forEach(function(c){D.m9[c.c]=c});_rdy();
}).catch(function(e){_dl.innerHTML='<div class="emp"><p>数据加载失败: '+e.message+'</p></div>'});
fetch('drg.json').then(function(r){return r.json()}).then(function(d){
_drg=d;_drg.mccS=new Set(d.mcc||[]);_drg.ccS=new Set(d.cc||[]);_drg.mccT=d.mcc_tbl||{};_drg.ccT=d.cc_tbl||{};if(D){D.no_dx=d.no_dx||[];D.no_px=d.no_px||[]};_drg._byMDC={};for(var ak in d.adrg_mdc){var am=d.adrg_mdc[ak];if(!_drg._byMDC[am.mdc])_drg._byMDC[am.mdc]={};var cat=am.cat.indexOf('外科')>=0?'S':(am.cat.indexOf('操作')>=0||am.cat.indexOf('手术室')>=0?'P':'M');if(!_drg._byMDC[am.mdc][cat])_drg._byMDC[am.mdc][cat]=[];_drg._byMDC[am.mdc][cat].push(ak)}
var ds=document.getElementById('ds2');if(ds)ds.innerHTML='<b style="color:var(--success)">已就绪</b> ('+Object.keys(d.dx2a||{}).length+'诊断 + '+Object.keys(d.px2a||{}).length+'手术)';_drg._linfenRW={};['MDCA','MDCB','MDCC','MDCD','MDCE','MDCF','MDCG','MDCH','MDCI','MDCJ','MDCK','MDCL','MDCM','MDCN','MDCO','MDCP','MDCQ','MDCR','MDCS','MDCT','MDCV','MDCW','MDCX','MDCY','MDCZ'].forEach(function(m){var rws={MDCA:[6.5,12.0],MDCB:[0.7,4.2],MDCC:[0.5,1.8],MDCD:[0.6,3.5],MDCE:[0.8,5.0],MDCF:[0.9,6.8],MDCG:[0.7,5.5],MDCH:[0.8,7.2],MDCI:[0.9,6.0],MDCJ:[0.4,2.5],MDCK:[0.5,1.6],MDCL:[0.6,3.0],MDCM:[0.5,2.8],MDCN:[0.5,3.2],MDCO:[0.3,1.8],MDCP:[0.8,8.5],MDCQ:[0.6,4.5],MDCR:[1.2,9.0],MDCS:[0.5,3.0],MDCT:[0.4,2.0],MDCV:[0.6,4.0],MDCW:[1.5,10.0],MDCX:[0.3,1.2],MDCY:[1.0,4.0],MDCZ:[1.5,12.0]};var rwRange=rws[m]||[0.5,3.0];for(var ak in d.adrg_mdc){var am=d.adrg_mdc[ak];if(am.mdc===m){var isSurg=am.cat.indexOf('外科')>=0;var base=isSurg?rwRange[1]*0.65:rwRange[0]+(rwRange[1]-rwRange[0])*0.2;base=Math.round(base*100)/100;var adj=1.0;if(ak[0]==='N'&&ak[1]==='C')adj=1.08;if(ak[0]==='P'&&ak[1]==='K')adj=1.06;if(ak[0]==='A')adj=0.95;var rw=Math.round(base*adj*100)/100;_drg._linfenRW[ak]=rw}}})
}).catch(function(e){var ds=document.getElementById('ds2');if(ds)ds.innerHTML='<b style="color:var(--danger)">加载失败</b>: '+e.message});

function st(n){
document.querySelectorAll('.tab').forEach(function(t){t.classList.remove('active')});
document.querySelectorAll('nav button').forEach(function(b){b.classList.remove('active')});
document.querySelectorAll('nav button').forEach(function(b,i){if((n==='icd10'&&i===0)||(n==='icd9'&&i===1)||(n==='drg'&&i===2)||(n==='dip'&&i===3)||(n==='convert'&&i===4))b.classList.add('active')});
var t=document.getElementById('t-'+n);if(t)t.classList.add('active');if(n==='drg')ldrg();
}

function s10(){if(!D)return;var q=document.getElementById('q10').value.trim(),lo=q.toLowerCase(),r=[];for(var i=0;i<D.icd10.length&&r.length<200;i++){var c=D.icd10[i];if(!q||c.c.toLowerCase().includes(lo)||c.n.includes(q)||c.n.toLowerCase().includes(lo))r.push(c)}document.getElementById('i10').textContent=q?'匹配 '+r.length:'共 '+D.icd10.length.toLocaleString();var cl=D.clin||{};document.getElementById('b10').innerHTML=r.length?r.map(function(c){var m=cl[c.c]||[],yc='<span class="tag ta">'+c.c+'</span>',cc,cn,cp='',gy='',bg='';if(!m.length){cc='<span style="color:#ccc">—</span>';cn='<span style="color:#ccc">无对照</span>';cp='<span style="color:#bbb">灰标</span>';gy=' style="opacity:.5"'}else{var x=m[0];cc='<span class="tag">'+x.cl+'</span>';cn='<span>'+x.cn+'</span>';if(c.c===x.cl&&c.n===x.cn)cp='<span style="color:var(--success)">✓</span>';else if(c.c===x.cl){cp='<span style="color:var(--warning)">⚠异名</span>';bg=' style="background:#fffdf5"';cc='<span class="tag" style="color:var(--warning)">'+x.cl+'</span>'}else if(c.n===x.cn){cp='<span style="color:var(--warning)">⚠异码</span>';bg=' style="background:#fffdf5"';cc='<span class="tag" style="color:var(--warning)">'+x.cl+'</span>'}else{cp='<span style="color:var(--danger)">✗不同</span>';bg=' style="background:#fff5f5"';cc='<span class="tag" style="color:var(--danger)">'+x.cl+'</span>'}}var mz=D.mt_zone||{},mt=mz[c.c]?' <span style="color:var(--warning);font-size:.75em">多发伤['+mz[c.c]+']</span>':'';var uns=c.n.indexOf('未特指')>=0?' <span style="color:#999;font-size:.75em">未特指</span>':'';var nd=new Set(D.no_dx||[]);var ng=nd.has(c.c)?'<span style="color:var(--danger);font-size:.78em">不作为主诊</span>':'<span style="font-size:.78em;color:var(--text-dim)">—</span>';var rid='r1'+c.c.replace(/[^a-zA-Z0-9]/g,'_');return '<tr id="'+rid+'"'+gy+bg+' onclick="t10(\''+rid+'\',\''+c.c+'\')"><td>'+yc+'</td><td>'+c.n+uns+mt+'</td><td>'+cc+'</td><td>'+cn+'</td><td style="font-size:.78em;white-space:nowrap">'+cp+'</td><td>'+ng+'</td></tr><tr id="h_'+rid+'" style="display:none;background:var(--bg-input)"><td colspan="6" id="hc_'+rid+'"></td></tr>'}).join(''):'<tr><td colspan="6" class="emp">未找到</td></tr>'}
var _codingRules=null,_codingRulesLoading=false;
function t10(rid,code){var nr=document.getElementById('h_'+rid);if(!nr)return;if(nr.style.display==='none'){nr.style.display='';
if(!_codingRules&&!_codingRulesLoading){_codingRulesLoading=true;fetch('coding_rules.json').then(function(r){return r.json()}).then(function(d){_codingRules=d;window._codingRules=d;console.log('Coding rules loaded: '+Object.keys(d.mutual_exclusion||{}).length+' mutex, '+Object.keys(d.combination_index||{}).length+' combo, '+Object.keys(d.additional_index||{}).length+' addl')})}
fetch('detail.json').then(function(r){return r.json()}).then(function(dt){D.h10=dt.h10||{};var h=D.h10[code];var hc=document.getElementById('hc_'+rid);if(h){var usp=function(n){return n&&n.indexOf('未特指')>=0?' <span style="color:#999;font-size:.85em">[未特指]</span>':''};var cn=_clinicalNotes[code];var cH='';if(cn){cH='<div style="margin-top:6px;padding:8px 14px;background:#fefce8;border-radius:6px;border-left:4px solid var(--warning);font-size:.76em"><b style="color:#92400e">📋 '+cn.n+'</b>';if(cn.s)cH+='<div style="margin-top:3px"><b>症状:</b> '+cn.s+'</div>';if(cn.l)cH+='<div><b>检验:</b> '+cn.l+'</div>';if(cn.i)cH+='<div><b>检查:</b> '+cn.i+'</div>';if(cn.r)cH+='<div style="margin-top:3px;color:var(--text-dim);font-size:.92em"><b>指南/共识:</b> '+cn.r.replace(/\|/g,'<br>')+'</div>';cH+='</div>'}

// Show coding rules if available
var rH='';var _cr=window._codingRules;
if(_cr){
  // 1. Mutual exclusion
  var me=_cr.mutual_exclusion&&_cr.mutual_exclusion[code];
  if(me&&me.length){
    rH+='<div style="margin-top:3px;padding:6px 10px;background:#fef0f0;border-radius:4px;border-left:3px solid var(--danger);font-size:.75em"><b style="color:var(--danger)">🚫 不能同时存在('+me.length+'个排除表)</b>';
    for(var mi=0;mi<Math.min(me.length,3);mi++){
      var tbl=_cr.exclusion_tables&&_cr.exclusion_tables[me[mi]];
      var cnt=tbl?tbl.codes.length:0;
      rH+='<div style="margin-top:2px">'+me[mi]+' ('+cnt+'条互斥编码)</div>';
    }
    rH+='</div>';
  }
  // 2. Combination codes
  var cb=_cr.combination_index&&_cr.combination_index[code];
  if(cb&&cb.length){
    rH+='<div style="margin-top:3px;padding:6px 10px;background:#e8f1fe;border-radius:4px;border-left:3px solid var(--accent);font-size:.75em"><b style="color:var(--accent)">🔀 合并编码规则</b>';
    for(var ci=0;ci<cb.length;ci++){rH+='<div style="margin-top:2px">'+cb[ci].desc+'</div><div style="color:var(--text-dim);font-size:.92em">→ '+cb[ci].action+'</div>';}
    rH+='</div>';
  }
  // 3. Additional codes
  var al=_cr.additional_index&&_cr.additional_index[code];
  if(al&&al.length){
    rH+='<div style="margin-top:3px;padding:6px 10px;background:#eef8f3;border-radius:4px;border-left:3px solid var(--success);font-size:.75em"><b style="color:var(--success)">➕ 附加编码规则</b>';
    for(var ai=0;ai<al.length;ai++){rH+='<div style="margin-top:2px">'+al[ai].desc+'</div><div style="color:var(--text-dim);font-size:.92em">→ '+al[ai].add_category+'</div>';}
    rH+='</div>';
  }
}
hc.innerHTML='<div style="padding:8px 16px;font-size:.75em;color:var(--text-dim)">亚目:<b>'+h.su+'</b> '+h.sun+usp(h.sun)+'→ 类目:<b>'+h.ca+'</b> '+h.can+usp(h.can)+'→ 节:<b>'+h.se+'</b> '+h.sen+'→ <b style="color:var(--accent)">第'+h.cno+'章</b>: '+h.chn+'</div>'+cH+rH}})}else nr.style.display='none'}

function cl9(code){var m=D.clin9||{};return m[code]||m[code+'00']||m[code+'000']||null}
function s9(){if(!D)return;var q=document.getElementById('q9').value.trim(),lo=q.toLowerCase(),r=[];for(var i=0;i<D.icd9.length&&r.length<200;i++){var c=D.icd9[i];if(!q||c.c.toLowerCase().includes(lo)||c.n.includes(q)||c.n.toLowerCase().includes(lo))r.push(c)}document.getElementById('i9').textContent=q?'匹配 '+r.length:'共 '+D.icd9.length.toLocaleString();document.getElementById('b9').innerHTML=r.length?r.map(function(c){var m=cl9(c.c),yc='<span class="tag ta">'+c.c+'</span>',cc,cn,ct='',en='',cp='',gy='',bg='';if(!m||!m.length){cc='<span style="color:#ccc">—</span>';cn='<span style="color:#ccc">无对照</span>';cp='<span style="color:#bbb">灰标</span>';gy=' style="opacity:.5"';ct='—';en='—'}else{var x=m[0];cc='<span class="tag">'+x.cl+'</span>';cn='<span>'+x.cn+'</span>';ct=x.cat?'<span style="font-size:.75em;padding:2px 6px;border-radius:10px;background:'+(CC[x.cat]||'#eee')+'">'+(CL[x.cat]||'')+' '+x.cat+'</span>':'—';en=x.e||'—';if(x.s)cp='<span style="color:var(--success)">✓</span>';else{cp='<span style="color:var(--warning)">⚠不同</span>';bg=' style="background:#fffdf5"';cc='<span class="tag" style="color:var(--warning)">'+x.cl+'</span>'}}var np=new Set(D.no_px||[]);var npg=np.has(c.c)?'<span style="color:var(--danger);font-size:.78em">不作为主手术</span>':'<span style="font-size:.78em;color:var(--text-dim)">—</span>';var rid='r9'+c.c.replace(/[^a-zA-Z0-9]/g,'_');return '<tr id="'+rid+'"'+gy+bg+' onclick="t9(\''+rid+'\',\''+c.c+'\')"><td>'+yc+'</td><td>'+c.n+'</td><td>'+cc+'</td><td>'+cn+'</td><td style="font-size:.78em;white-space:nowrap">'+cp+'</td><td>'+ct+'</td><td>'+en+'</td><td>'+npg+'</td></tr><tr id="h_'+rid+'" style="display:none;background:var(--bg-input)"><td colspan="8" id="hc_'+rid+'"></td></tr>'}).join(''):'<tr><td colspan="8" class="emp">未找到</td></tr>'}
function t9(rid,code){var nr=document.getElementById('h_'+rid);if(!nr)return;if(nr.style.display==='none'){nr.style.display='';fetch('detail.json').then(function(r){return r.json()}).then(function(dt){D.h9=dt.h9||{};D.lead=dt.lead||{};var h=D.h9[code],lk=code.match(/^\d+\.\d{2}/);lk=lk?lk[0]:code;var ls=D.lead[lk]||[],hc=document.getElementById('hc_'+rid),hl='';if(h)hl+='<div style="padding:2px 16px;font-size:.75em;color:var(--text-dim)">细目:<b>'+h.det+'</b> '+h.det_n+'→ 亚目:<b>'+h.sub+'</b> '+h.sub_n+'→ 类目:<b>'+h.cat+'</b> '+h.cat_n+'→ <b style="color:var(--accent)">第'+h.ch_no+'章</b>: '+h.ch_n+'</div>';if(ls.length){hl+='<div style="padding:2px 16px;font-size:.75em;color:var(--text-dim)"><br>主导词('+ls.length+'条):<br><div style="margin-top:4px;max-height:380px;overflow:auto;border:1px solid var(--border);border-radius:4px;padding:6px 8px;background:var(--bg);display:flex;flex-wrap:wrap;gap:2px 16px">'+ls.map(function(l,i){return '<div style="font-size:.75em;padding:2px 0;color:var(--text-dim);white-space:nowrap">'+(i+1)+'. '+l.p+'</div>'}).join('')+'</div></div>'}if(!h&&!ls.length)hl='<div style="padding:8px 16px;font-size:.75em;color:var(--text-dim)">加载中...</div>';hc.innerHTML=hl})}else nr.style.display='none'}

//========== DRG ==========
var _dx=[],_dx2=[],_px=[],_px2=[],_st=null;
function ldrg(){
if(!_drg){var ds=document.getElementById('ds2');if(ds)ds.innerHTML='<span style="color:var(--warning)">加载中(389KB)...</span>'}
}
function f10(q,n){n=n||200;var lo=q.toLowerCase(),r=[],keys=Object.keys((_drg||{}).dx2a||{});for(var i=0;i<keys.length;i++){var c=D.m10[keys[i]];if(c&&(c.c.toLowerCase().startsWith(lo)||c.n.includes(q)))r.push(c)}return r.slice(0,n)}
function f10all(q,n){n=n||200;var lo=q.toLowerCase(),r=[];for(var i=0;i<D.icd10.length;i++){var c=D.icd10[i];if(c.c.toLowerCase().startsWith(lo)||c.n.includes(q)){r.push(c);if(r.length>=n)break}}return r}
function f9all(q,n){n=n||200;var lo=q.toLowerCase(),r=[];for(var i=0;i<D.icd9.length;i++){var c=D.icd9[i];if(c.c.toLowerCase().startsWith(lo)||c.n.includes(q)){r.push(c);if(r.length>=n)break}}return r}
function f9(q,n){n=n||200;var lo=q.toLowerCase(),r=[],keys=Object.keys((_drg||{}).px2a||{});for(var i=0;i<keys.length;i++){var c=D.m9[keys[i]];if(c&&(c.c.toLowerCase().startsWith(lo)||c.n.includes(q)))r.push(c)}return r.slice(0,n)}
function sdx(iid,bid){clearTimeout(_st);_st=setTimeout(function(){var q=document.getElementById(iid).value.trim(),box=document.getElementById(bid);if(!q||q.length<1){box.style.display='none';return}ldrg();var m=_drg?f10(q):f10all(q);if(!m.length){box.style.display='none';return}box.style.display='block';var fn=iid==='di'?'adx':'adx2';var mtZ=(_drg||{}).mt_zone||{},greyS=new Set((_drg||{}).grey||[]),mccS=_drg?_drg.mccS:new Set,ccS=_drg?_drg.ccS:new Set,excl=_drg?_drg.excl:{};box.innerHTML=m.map(function(c){var tags='';if(mccS.has(c.c))tags+='<span style="color:var(--danger);font-weight:600;font-size:.72em">MCC</span> ';else if(ccS.has(c.c))tags+='<span style="color:var(--warning);font-size:.72em">CC</span> ';if(greyS.has(c.c))tags+='<span style="color:#bbb;font-size:.72em">灰码</span> ';var mtt=mtZ[c.c]?' <span style="color:var(--warning);font-size:.72em">多发伤['+mtZ[c.c]+']</span> ':'';var et='';for(var k in excl){if(excl[k].indexOf(c.c)>=0){et=k;break}}return '<div class="si" onclick="document.getElementById(\''+bid+'\').style.display=\'none\';'+fn+'(\''+c.c+'\',\''+c.n.replace(/'/g,'\\\x27')+'\')"><span class="sc">'+c.c+'</span><span class="sn">'+c.n+'</span>'+mtt+tags+'<span style="font-size:.7em;color:var(--text-dim);margin-left:4px">'+(et||'')+'</span></div>'}).join('')},200)}
function spx(iid,bid){clearTimeout(_st);_st=setTimeout(function(){var q=document.getElementById(iid).value.trim(),box=document.getElementById(bid);if(!q||q.length<1){box.style.display='none';return}var m=_drg?f9(q):f9all(q);if(!m.length){box.style.display='none';return}box.style.display='block';var fn=iid==='pi'?'apx':'apx2';box.innerHTML=m.map(function(c){return '<div class="si" onclick="document.getElementById(\''+bid+'\').style.display=\'none\';'+fn+'(\''+c.c+'\',\''+c.n.replace(/'/g,'\\\x27')+'\')"><span class="sc">'+c.c+'</span><span class="sn">'+c.n+'</span></div>'}).join('')},200)}
function _firstSug(bid){var box=document.getElementById(bid);if(box.style.display!=='none'){var si=box.querySelector('.si');if(si){var sc=si.querySelector('.sc'),sn=si.querySelector('.sn');if(sc&&sn)return{c:sc.textContent.trim(),n:sn.textContent.trim()}}}return null}
function adx(c,n){if(!c){var fs=_firstSug('ds');if(fs){c=fs.c;n=fs.n}else{var i=document.getElementById('di'),q=i.value.trim().toUpperCase();var f=D.m10[q]||f10(q,1)[0];if(f){c=f.c;n=f.n}}document.getElementById('di').value=''}if(c){_dx=[{c:c,n:n}];rc();document.getElementById('ds').style.display='none'}}
function adx2(c,n){if(!c){var fs=_firstSug('d2s');if(fs){c=fs.c;n=fs.n}else{var i=document.getElementById('d2'),q=i.value.trim().toUpperCase();var f=D.m10[q]||f10(q,1)[0];if(f){c=f.c;n=f.n}}document.getElementById('d2').value=''}if(c){_dx2.push({c:c,n:n});rc();document.getElementById('d2s').style.display='none'}}
function apx(c,n){if(!c){var fs=_firstSug('ps');if(fs){c=fs.c;n=fs.n}else{var i=document.getElementById('pi'),q=i.value.trim();var f=D.m9[q]||f9(q,1)[0];if(f){c=f.c;n=f.n}}document.getElementById('pi').value=''}if(c){_px=[{c:c,n:n}];rc();document.getElementById('ps').style.display='none'}}
function apx2(c,n){if(!c){var fs=_firstSug('p2s');if(fs){c=fs.c;n=fs.n}else{var i=document.getElementById('p2'),q=i.value.trim();var f=D.m9[q]||f9(q,1)[0];if(f){c=f.c;n=f.n}}document.getElementById('p2').value=''}if(c){_px2.push({c:c,n:n});rc();document.getElementById('p2s').style.display='none'}}
function rc(){
var gs=new Set((_drg||{}).grey||[]);
function tag(d){var t='';if(gs.has(d.c))t+=' <span style="color:#bbb;font-size:.7em">灰</span>';return t}
document.getElementById('dc').innerHTML=_dx.map(function(d){return'<span class="chip chip-p">⭐ '+d.c+' '+d.n+tag(d)+' <span class="chip-x" onclick="_dx=[];rc()">×</span></span>'}).join('');
document.getElementById('d2c').innerHTML=_dx2.map(function(d,i){return'<span class="chip">'+d.c+' '+d.n+tag(d)+' <span class="chip-x" onclick="_dx2.splice('+i+',1);rc()">×</span></span>'}).join('');
document.getElementById('pc').innerHTML=_px.map(function(p){return'<span class="chip chip-p">⭐ '+p.c+' '+p.n+' <span class="chip-x" onclick="_px=[];rc()">×</span></span>'}).join('');
document.getElementById('p2c').innerHTML=_px2.map(function(p,i){return'<span class="chip">'+p.c+' '+p.n+' <span class="chip-x" onclick="_px2.splice('+i+',1);rc()">×</span></span>'}).join('')}

function calAge(){function pd(s){s=s.trim();if(/^\d{8}$/.test(s))s=s.slice(0,4)+'-'+s.slice(4,6)+'-'+s.slice(6,8);return s}var b=pd(document.getElementById('bdt').value),a=pd(document.getElementById('adt').value),disp=document.getElementById('age-disp');if(b&&a){var bd=new Date(b),ad=new Date(a);if(isNaN(bd)||isNaN(ad)){disp.innerHTML='';return}var diffDays=Math.floor((ad-bd)/86400000);if(diffDays<0){disp.innerHTML='<span style="color:var(--danger)">日期错误</span>';return}var yrs=Math.floor(diffDays/365.25),remDays=diffDays%365;var txt='';if(yrs>=1)txt=yrs+'岁';else if(diffDays>=29)txt=Math.floor(diffDays/30)+'月('+diffDays+'天)';else txt=diffDays+'天(新生儿)';disp.innerHTML=txt+(yrs>=1?'':' <span style="font-size:.75em;color:var(--text-dim);font-weight:400">'+diffDays+'天</span>')}else{disp.innerHTML=''}}
function dr(){
	if(!_dx.length&&!_px.length){document.getElementById('drr').innerHTML='<div class="emp"><p>请先添加诊断和手术编码</p><p style="font-size:.78em;color:var(--text-dim)">_dx='+_dx.length+' _px='+_px.length+' D='+!!D+' _drg='+!!_drg+'</p></div>';return}
	if(!_drg){ldrg();document.getElementById('drr').innerHTML='<div class="emp"><p>DRG数据加载中...</p></div>';setTimeout(function(){if(_drg)dr();else document.getElementById('drr').innerHTML='<div class="emp"><p>数据加载失败，请刷新重试</p></div>'},2000);return}
	var pd=_dx[0],pp=_px[0],ca=new Map();
		console.log('DRG: pd='+(pd?pd.c:'none')+', pp='+(pp?pp.c:'none')+', dx2='+_dx2.length+', px2='+_px2.length);
		function lookDx(code){var m=_drg.dx2a[code];if(m){console.log('  lookDx exact: '+code+' -> '+m.length);return m}var b=code.match(/^([A-Z]\d{2}\.\d+)/);if(b){var k=b[1]+'x001';m=_drg.dx2a[k];if(m){console.log('  lookDx x001: '+code+' -> '+k+' -> '+m.length);return m}m=_drg.dx2a[b[1]];if(m){console.log('  lookDx base: '+code+' -> '+b[1]+' -> '+m.length);return m}}m=_drg.dx2a[code+'x001'];if(m)console.log('  lookDx fb: '+code+' -> '+code+'x001 -> '+m.length);return m||[]}
		function lookPx(code){var m=_drg.px2a[code];if(m){console.log('  lookPx exact: '+code+' -> '+m.length);return m}if(code.indexOf('.')>0){var p=code.split('.'),base=p[0]+'.'+p[1].substring(0,2);m=_drg.px2a[base];if(m)console.log('  lookPx short: '+code+' -> '+base+' -> '+m.length);return m||[]}return[]}
		var _gdr=document.getElementById('gdr').value,_gdrNote='',gdrNote='';
		// === CHS-DRG 2.0 规则引擎 ===
		function filterGender(k){if(_gdr==='M'&&'NO'.indexOf(k[0])>=0){if(!_gdrNote)_gdrNote='已按性别过滤';gdrNote=_gdrNote;return true}if(_gdr==='F'&&k[0]==='M'){if(!_gdrNote)_gdrNote='已按性别过滤';gdrNote=_gdrNote;return true}return false}
		// Tumor type detection
		var _tt=null;if(pd){var c0=pd.c.toUpperCase();if(/^C[0-9]/.test(c0)||/^D3[7-9]/.test(c0)||/^D4[0-8]/.test(c0))_tt='malignant';else if(/^D0[0-9]/.test(c0))_tt='insitu';else if(/^D1[0-9]/.test(c0)||/^D2[0-9]/.test(c0)||/^D3[0-6]/.test(c0))_tt='benign';}
		function adrgTumorAlign(adrgName,tt){if(!tt||!adrgName)return 0;var n=adrgName;if(tt==='malignant'){if(n.indexOf('恶性')>=0||n.indexOf('化学')>=0||n.indexOf('放射')>=0)return 1;if(n.indexOf('良性')>=0)return -1;}if(tt==='benign'){if(n.indexOf('良性')>=0)return 1;if(n.indexOf('恶性')>=0)return -1;}return 0;}
		// Phase 0: Pre-MDC check (CHS-DRG 2.0 先期分组)
		// MDCA: transplant, tracheostomy+vent≥96h, ECMO
		var preMDC=null;
		var allDx=[pd].concat(_dx2),allPx=[pp].concat(_px2);
		var hasVent96=false,hasEcmo=false;
		// Check vent≥96h from time inputs
		var vtRows=document.querySelectorAll('#ventList .time-row');
		vtRows.forEach(function(r){var sel=r.querySelector('select');if(sel&&sel.value==='invasive'){var inps=r.querySelectorAll('input');var s=inps[0].value,e=inps[1].value;if(s&&e){var h=Math.floor((new Date(e)-new Date(s))/(1000*60*60));if(h>=96)hasVent96=true;}}});
		var ecmoRows=document.querySelectorAll('#ecmoList .time-row');
		ecmoRows.forEach(function(r){var inps=r.querySelectorAll('input');if(inps[0].value&&inps[1].value)hasEcmo=true;});
		// Check if any matched ADRG is in MDCA
		for(var pi=0;pi<allPx.length;pi++){if(!allPx[pi])continue;var pm2=lookPx(allPx[pi].c);for(var pj=0;pj<pm2.length;pj++){var mad=pm2[pj].a;var md2=_drg.adrg_mdc[mad];if(md2&&md2.mdc==='MDCA'){preMDC={mdc:'MDCA',adrg:mad,info:pm2[pj],reason:''};
			if(hasVent96&&mad==='AH2')preMDC.reason='气管切开+有创呼吸机≥96h→MDCA先期分组';
			else if(hasEcmo&&mad==='AH1')preMDC.reason='ECMO支持→MDCA先期分组';
			else if(mad==='AA1'||mad==='AB1'||mad==='AC1'||mad==='AD1'||mad==='AE1'||mad==='AF1'||mad==='AG1'||mad==='AG2')preMDC.reason='器官/组织移植→MDCA先期分组';
			break;}}if(preMDC)break;}
		// Phase 1: Determine MDCs
		var dxMDC='',pxMDC='';if(pd){var dm=lookDx(pd.c);if(dm.length>0)dxMDC=dm[0].a[0]}if(pp){var pm=lookPx(pp.c);if(pm.length>0)pxMDC=pm[0].a[0]}
		if(preMDC){dxMDC='A';pxMDC='A';}
		var isQY=!!(dxMDC&&pxMDC&&dxMDC!==pxMDC);
		// Phase 2: Collect ADRGs by MDC+category for primary dx and px
		var byMDC={};function addToMDC(mdc,cat,adrg,info,matchedBy,ta,isPrimary){var key=mdc+'|'+cat;if(!byMDC[key])byMDC[key]={mdc:mdc,cat:cat,adrgs:{}};var a=byMDC[key].adrgs;if(!a[adrg])a[adrg]={an:info.an,drgs:info.d||[],matched:[],_ta:0,_primary:0};if(a[adrg].matched.indexOf(matchedBy)<0)a[adrg].matched.push(matchedBy);if(ta&&ta>a[adrg]._ta)a[adrg]._ta=ta;if(isPrimary)a[adrg]._primary=1;}
		// Collect dx-matched ADRGs: primary dx first, then other dx, then main proc, then other procs
		[['P',pd,true]].concat(_dx2.map(function(d){return['S',d,false]}),[[null,pp,true]],_px2.map(function(p){return['s',p,false]})).forEach(function(x){var d=x[1];if(!d)return;var isPrim=x[2];var matches=x[0]==='P'||x[0]==='S'?lookDx(d.c):lookPx(d.c);matches.forEach(function(a){var k=a.a;if(filterGender(k))return;var md=_drg.adrg_mdc[k]||{};var mdc=md.mdc||k[0];var cat=md.cat||'';var c=cat.indexOf('外科')>=0?'S':(cat.indexOf('操作')>=0||cat.indexOf('手术室')>=0?'P':'M');var ta=(x[0]==='P')?adrgTumorAlign(a.an,_tt):0;addToMDC(mdc,c,k,a,x[0]==='P'?'主诊:'+d.c:(x[0]==='S'?'其他诊:'+d.c:(x[0]===null?'主手术:'+d.c:'其他手术:'+d.c)),ta,isPrim)})
		})
		// Phase 3: Priority-based selection (CHS-DRG 2.0 Table 1.1 rules)
		// Priority within an MDC: S(外科) > P(操作) > M(内科)
		// For QY: surgical MDC takes priority
		function pickBest(mdcToCheck){
			var cats=['MDC'+mdcToCheck+'|S','MDC'+mdcToCheck+'|P','MDC'+mdcToCheck+'|M'];
			// First pass: only consider ADRGs matched by primary dx or primary procedure
			for(var ci=0;ci<cats.length;ci++){
				var entry=byMDC[cats[ci]];if(!entry)continue;
				var result={mdc:entry.mdc,cat:entry.cat==='S'?'外科部分':(entry.cat==='P'?'非手术室操作部分':'内科部分'),adrgs:[],primary:null,path:[]};
				for(var ak in entry.adrgs){
					var a=entry.adrgs[ak];
					var hasPD=pd&&lookDx(pd.c).some(function(x){return x.a===ak});
					var hasPP=pp&&lookPx(pp.c).some(function(x){return x.a===ak});
					// Only include ADRGs matched by primary dx or primary procedure in first pass
					if(!hasPD&&!hasPP&&!a._primary)continue;
					result.adrgs.push({code:ak,name:a.an,drgs:a.drgs,matched:a.matched,hasPD:hasPD,hasPP:hasPP,_ta:a._ta||0,_primary:a._primary||0});
				}
				if(result.adrgs.length>0){
					result.adrgs.sort(function(a,b){
						if(a._ta!==b._ta)return b._ta-a._ta;
						var sa=(a.hasPP?3:0)+(a.hasPD?1:0);var sb=(b.hasPP?3:0)+(b.hasPD?1:0);
						if(sa!==sb)return sb-sa;
						return 0;
					});
					result.primary=result.adrgs[0];
					result.path.push('MDC'+mdcToCheck);result.path.push(result.cat);
					if(_tt&&result.primary._ta<0)result.path.push('⚠ 肿瘤类型不匹配');
					if(result.primary.hasPP)result.path.push('主手术'+pp.c+'直接匹配→'+result.primary.code);
					else if(result.primary.hasPD)result.path.push('主诊'+pd.c+'直接匹配→'+result.primary.code);
					else result.path.push('间接匹配→'+result.primary.code);
					return result;
				}
			}
			// Second pass: no primary match found, fall back to secondary diagnosis matches
			for(var ci=0;ci<cats.length;ci++){
				var entry=byMDC[cats[ci]];if(!entry)continue;
				var result={mdc:entry.mdc,cat:entry.cat==='S'?'外科部分':(entry.cat==='P'?'非手术室操作部分':'内科部分'),adrgs:[],primary:null,path:[]};
				for(var ak in entry.adrgs){
					var a=entry.adrgs[ak];
					var hasPD=pd&&lookDx(pd.c).some(function(x){return x.a===ak});
					var hasPP=pp&&lookPx(pp.c).some(function(x){return x.a===ak});
					result.adrgs.push({code:ak,name:a.an,drgs:a.drgs,matched:a.matched,hasPD:hasPD,hasPP:hasPP,_ta:a._ta||0,_primary:a._primary||0});
				}
				if(result.adrgs.length>0){
					result.adrgs.sort(function(a,b){
						var sa=(a.hasPP?3:0)+(a.hasPD?1:0);var sb=(b.hasPP?3:0)+(b.hasPD?1:0);
						if(sa!==sb)return sb-sa;
						return 0;
					});
					result.primary=result.adrgs[0];
					result.path.push('MDC'+mdcToCheck);result.path.push(result.cat);
					result.path.push('(次要诊断匹配)');
					return result;
				}
			}
			return null;
		}
		// Main decision flow
		var decision=preMDC?null:pickBest(dxMDC);var decisionNote='';var qyDecision=null;var qyPath='';
		if(preMDC){
			// Pre-MDC: direct routing
			decision={mdc:'MDCA',cat:preMDC.reason,adrgs:[],primary:{code:preMDC.adrg,name:preMDC.info.an,drgs:preMDC.info.d||[],hasPD:false,hasPP:true,matched:['先期分组: '+preMDC.reason],_ta:0},path:['先期分组',preMDC.reason]};
		}
		if(!decision&&!preMDC&&isQY&&pxMDC){decision=pickBest(pxMDC);if(decision){decisionNote='主诊MDC'+dxMDC+'≠手术MDC'+pxMDC+'，按手术路径优先入组';qyPath='主诊→MDC'+dxMDC+' | 主手术→MDC'+pxMDC+' → 手术优先';}}
		if(!decision&&!preMDC&&isQY){decision=pickBest(dxMDC);if(decision)decisionNote='手术路径无匹配，按诊断路径入MDC'+dxMDC}
		// Phase 4: MCC/CC exclusion for primary ADRG
		var mccInfo={mccDx:[],ccDx:[],exDx:[],effS:'noCC'};
		if(decision&&decision.primary&&pd){
			var primaryAdrg=decision.primary;
			var mccS=_drg.mccS||new Set,ccS=_drg.ccS||new Set,mccT=_drg.mccT||{},ccT=_drg.ccT||{},excl=_drg.excl||{};
			_dx2.forEach(function(d){
				if(mccS.has(d.c)){var tbl=mccT[d.c]||'',exclCodes=excl[tbl]||[];if(!pd||exclCodes.indexOf(pd.c)<0){mccInfo.mccDx.push(d.c)}else{mccInfo.exDx.push(d.c)}}
				else if(ccS.has(d.c)){var tbl2=ccT[d.c]||'',exclCodes2=excl[tbl2]||[];if(!pd||exclCodes2.indexOf(pd.c)<0){mccInfo.ccDx.push(d.c)}else{mccInfo.exDx.push(d.c)}}
			});
			mccInfo.effS=mccInfo.mccDx.length>0?'MCC':(mccInfo.ccDx.length>0?'CC':'noCC');
			// Select final DRG
			var drgs=primaryAdrg.drgs||[];var finalD=drgs[0];for(var j=0;j<drgs.length;j++){if(drgs[j].s===mccInfo.effS){finalD=drgs[j];break}}
			primaryAdrg.finalDRG=finalD||drgs[0];
		}
		// Phase 5: Display
		function showAdrg(adrg,isPrimary,mccInfo){
			var md=_drg.adrg_mdc[adrg.code]||{};var cat=(md.cat||'').indexOf('外科')>=0?'外科':((md.cat||'').indexOf('操作')>=0?'操作':'内科');
			var catBg=cat==='外科'?'var(--danger)':(cat==='操作'?'var(--warning)':'var(--accent)');
			var finalD=adrg.finalDRG||adrg.drgs[0];
			var effS=mccInfo?mccInfo.effS:(finalD?finalD.s:'noCC');
			var h='<div style="'+(isPrimary?'background:rgba(59,125,224,.06);border:1px solid var(--accent);border-left:4px solid var(--accent);':'background:var(--bg);border:1px solid var(--border);')+'border-radius:var(--r);padding:12px;margin-bottom:8px">';
			h+='<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:6px"><b style="font-size:1.15em;color:'+(isPrimary?'var(--accent)':'var(--text)')+'">'+finalD.c+'</b><span>'+finalD.n+'</span><span style="font-size:.7em;padding:2px 8px;border-radius:10px;background:'+catBg+';color:#fff;font-weight:600">'+cat+'</span>';
			if(mccInfo&&mccInfo.effS!=='noCC')h+='<span style="font-size:.72em;padding:1px 6px;border-radius:6px;background:'+(mccInfo.effS==='MCC'?'var(--danger)':'var(--warning)')+';color:#fff">'+mccInfo.effS+'</span>';
			if(isPrimary)h+='<span style="font-size:.7em;padding:1px 6px;border-radius:6px;background:var(--success);color:#fff">推荐</span>';
			h+='</div>';
			// ADRG info
			h+='<div style="font-size:.72em;color:var(--text-dim);margin-bottom:4px">ADRG '+adrg.code+' '+adrg.name+' | MDC '+md.mdc+' '+md.mdc_n+'</div>';
			// Match info
			if(adrg.matched&&adrg.matched.length>0)h+='<div style="font-size:.75em;color:var(--text-dim)">匹配: '+adrg.matched.join(' | ')+'</div>';
			// DRG variants
			if(adrg.drgs&&adrg.drgs.length>1)h+='<div style="font-size:.7em;color:var(--text-dim);margin-top:4px">所有DRG: '+adrg.drgs.map(function(d){var c2=d.s===effS?'var(--accent)':'var(--text-dim)';return'<span style="font-family:monospace;color:'+c2+';'+(d.s===effS?'font-weight:700':'')+'">'+d.c+' '+d.n+' ['+d.s+']</span>'}).join(' | ')+'</div>';
			// MCC/CC info
			if(mccInfo)h+='<div style="font-size:.75em;margin-top:4px">'+(mccInfo.mccDx.length?'<span style="color:var(--danger)">MCC: '+mccInfo.mccDx.join(', ')+'</span> ':'')+(mccInfo.ccDx.length?'<span style="color:var(--warning)">CC: '+mccInfo.ccDx.join(', ')+'</span> ':'')+(mccInfo.exDx.length?'<span style="color:var(--text-dim);text-decoration:line-through">排除: '+mccInfo.exDx.join(', ')+'</span>':'')+'</div>';var isLF=document.getElementById('drg-ver').value==='linfen';if(isLF&&adrg.code){var rw=_drg._linfenRW&&_drg._linfenRW[adrg.code]||1.0;var hl=document.getElementById('hosp-lv');var hcoef=hl?({3:1.0,2:0.8,1:0.6}[hl.value]||1.0):1.0;h+='<div style="font-size:.75em;margin-top:6px;padding-top:6px;border-top:1px dotted var(--border);display:flex;gap:14px;flex-wrap:wrap"><span>权重 <b style="color:var(--accent)">'+rw+'</b></span><span>费率 <b>4,676.74</b> 元/权重</span><span>预计支付 <b style="color:var(--success)">'+Math.round(rw*4676.74*hcoef).toLocaleString()+'</b> 元</span><span style="font-size:.72em;color:var(--text-dim)">系数'+hcoef.toFixed(1)+'</span></div>';}
			h+='</div>';return h
		}
		var mdcNames={};for(var mk in _drg.adrg_mdc){var mv=_drg.adrg_mdc[mk];if(!mdcNames[mv.mdc])mdcNames[mv.mdc]=mv.mdc_n};var drgHTML='';var titleHTML='';
			if(decision&&decision.primary){
				titleHTML='<h3 style="color:'+(preMDC?'var(--warning)':'var(--success)')+'">'+(preMDC?'⚡ 先期分组: ':'入组结果: ')+decision.primary.finalDRG.c+' '+decision.primary.finalDRG.n+'</h3>';
				if(_tt&&decision.primary._ta<0)titleHTML+='<div style="font-size:.78em;color:var(--danger);padding:4px 8px;background:rgba(232,85,85,.08);border-left:3px solid var(--danger);margin:8px 0">⚠ 肿瘤类型不匹配：主诊为'+(pd?pd.c+' '+pd.n:'')+'（'+(_tt==='benign'?'良性':'恶性')+'），推荐核实ADRG是否适用</div>';
				// Decision path
				drgHTML+='<div style="font-size:.78em;color:var(--text-dim);margin-bottom:12px;padding:8px 12px;background:var(--bg);border:1px solid var(--border);border-radius:6px">';
				drgHTML+='<b>入组路径:</b> '+decision.path.join(' → ')+(isQY?'<br><span style="color:var(--warning)">QY歧义: 主诊→MDC'+dxMDC+'('+(mdcNames[dxMDC]||'')+') | 主手术→MDC'+pxMDC+'('+(mdcNames[pxMDC]||'')+') → 按CHS-DRG规则，外科/操作组优先</span>':'');
				if(decisionNote)drgHTML+='<br><span style="color:var(--warning)">'+decisionNote+'</span>';
				drgHTML+='</div>';
				// QY analysis panel
				if(isQY){
					drgHTML+='<details open style="margin-bottom:10px"><summary style="cursor:pointer;font-size:.82em;font-weight:600;color:var(--warning);padding:4px 0"> QY 歧义分析：主诊MDC'+dxMDC+' vs 手术MDC'+pxMDC+'</summary>';
					drgHTML+='<div style="margin-top:6px;padding:8px 10px;background:rgba(212,120,47,.04);border:1px solid var(--warning);border-radius:6px;font-size:.78em">';
					drgHTML+='<div style="margin-bottom:6px"><b>编码冲突:</b> 主诊 '+pd.c+' '+pd.n+' 指向MDC'+dxMDC+(mdcNames[dxMDC]?'('+mdcNames[dxMDC]+')':'')+'，主手术 '+pp.c+' '+pp.n+' 指向MDC'+pxMDC+(mdcNames[pxMDC]?'('+mdcNames[pxMDC]+')':',')+'，不在同一MDC</div>';
					drgHTML+='<div style="margin:8px 0;display:flex;gap:12px;flex-wrap:wrap">';
					// Surgery path
					drgHTML+='<div style="flex:1;min-width:180px;padding:8px;background:var(--bg);border:2px solid var(--accent);border-radius:6px"><div style="font-size:.85em;font-weight:600;color:var(--accent);margin-bottom:4px">当前路径（手术优先）</div><div style="font-size:.92em">MDC'+pxMDC+' '+decision.cat+'</div><div style="font-size:.85em;color:var(--success);margin-top:2px">→ '+decision.primary.code+' '+decision.primary.name+'</div><div style="font-size:.72em;color:var(--text-dim);margin-top:4px">CHS-DRG规则：外科组/操作组以手术编码为分组第一依据，主诊MDC不一致时优先按手术路径入组</div></div>';
					// Diagnosis path alternatives
					var dxPathAdrgs=[];['MDC'+dxMDC+'|S','MDC'+dxMDC+'|P','MDC'+dxMDC+'|M'].forEach(function(key){if(byMDC[key]){var entry=byMDC[key];for(var ak in entry.adrgs){if(dxPathAdrgs.length<4)dxPathAdrgs.push({code:ak,name:entry.adrgs[ak].an})}}});
					drgHTML+='<div style="flex:1;min-width:180px;padding:8px;background:var(--bg);border:2px solid var(--border);border-radius:6px"><div style="font-size:.85em;font-weight:600;color:var(--text-dim);margin-bottom:4px">备选路径（主诊MDC'+dxMDC+'）</div><div style="font-size:.92em;color:var(--text-dim)">'+decision.path.join(' → ')+'</div>'+(dxPathAdrgs.length?'<div style="font-size:.78em;color:var(--text-dim);margin-top:4px">主诊MDC候选：'+dxPathAdrgs.map(function(a){return a.code+' '+a.name}).join(' / ')+'</div>':'<div style="font-size:.78em;color:var(--text-dim)">主诊MDC内无匹配ADRG</div>')+'</div>';
					drgHTML+='</div>';
					// Recommendation
					var isSurgical=decision.cat.indexOf('外科')>=0||decision.cat.indexOf('操作')>=0;
					drgHTML+='<div style="margin-top:8px;padding:8px;background:var(--bg);border-radius:6px">';
					drgHTML+='<b style="color:var(--accent)">建议:</b><br>';
					if(isSurgical){
						drgHTML+='<span style="color:var(--success)">✓</span> 如手术为主要治疗手段 → 维持当前手术路径入组<br>';
						drgHTML+='<span style="color:var(--text-dim)">•</span> 如保守治疗（手术为次要或诊断性操作）→ 可考虑主诊路径入内科组<br>';
						drgHTML+='<span style="color:var(--text-dim)">•</span> QY歧义组按手术所在MDC最低权重结算，编码员可结合临床实际情况调整主诊或主手术编码';
					}else{
						drgHTML+='<span style="color:var(--accent)">•</span> 当前按诊断路径入组，手术跨MDC匹配<br>';
						drgHTML+='<span style="color:var(--text-dim)">•</span> 建议核实：1) 主手术编码是否准确 2) 是否存在更合适的主诊编码<br>';
						drgHTML+='<span style="color:var(--text-dim)">•</span> QY歧义组按所在MDC最低权重结算';
					}
					drgHTML+='</div></div></details>';
				}
				// Show primary recommendation
				drgHTML+=showAdrg(decision.primary,true,mccInfo);
				// Show other candidates in same MDC+category
				var others=decision.adrgs.filter(function(a){return a.code!==decision.primary.code});
				if(others.length>0){drgHTML+='<div style="font-size:.75em;color:var(--text-dim);margin:8px 0 4px 0">同组其他候选 ('+others.length+'):</div>';others.forEach(function(a){drgHTML+=showAdrg(a,false)})}
				// Show alternatives from other categories in same MDC
				var pmdc=decision.mdc||dxMDC;var alts=[];['MDC'+pmdc+'|P','MDC'+pmdc+'|M','MDC'+pmdc+'|S'].forEach(function(key){if(byMDC[key]&&key!=='MDC'+pmdc+'|'+decision.cat.slice(0,1)){var entry=byMDC[key];for(var ak in entry.adrgs){alts.push({code:ak,name:entry.adrgs[ak].an,drgs:entry.adrgs[ak].drgs,matched:entry.adrgs[ak].matched,cat:entry.cat})}}})
				if(alts.length>0){drgHTML+='<div style="font-size:.75em;color:var(--text-dim);margin:8px 0 4px 0">同MDC其他类别候选 ('+alts.length+'):</div>';alts.slice(0,5).forEach(function(a){drgHTML+=showAdrg(a,false)})}}else{titleHTML='<h3 style="color:var(--danger)">未找到匹配的 ADRG 分组</h3>';drgHTML+='<div style="font-size:.82em;color:var(--text-dim)">主诊:'+(pd?pd.c+' '+pd.n:'—')+' | 主手术:'+(pp?pp.c+' '+pp.n:'—')+'</div>';if(!dxMDC)drgHTML+='<div style="font-size:.78em;color:var(--text-dim);margin-top:4px">诊断编码不在 CHS-DRG 2.0 范围内</div>';else{drgHTML+='<div style="font-size:.78em;color:var(--text-dim);margin-top:4px">诊断属于MDC'+dxMDC+'，但未匹配到ADRG（可能为0000组或编码不在数据范围内）</div>';if(isQY)drgHTML+='<div style="font-size:.78em;color:var(--warning);margin-top:4px">QY歧义检测: 主诊MDC'+dxMDC+'≠手术MDC'+pxMDC+'</div>'}}
		// No-group diagnosis warnings
		var noDx=new Set(_drg.no_dx||[]),noPx=new Set(_drg.no_px||[]),ng='';
		_dx.forEach(function(d){if(noDx.has(d.c))ng+='<div style="font-size:.78em;color:var(--danger);margin:2px 0"> 不作为主诊: '+d.c+' '+d.n+'</div>'});
		_dx2.forEach(function(d){if(noDx.has(d.c))ng+='<div style="font-size:.78em;color:var(--danger);margin:2px 0"> 不作为主诊: '+d.c+' '+d.n+'</div>'});
		_px.forEach(function(p){if(noPx.has(p.c))ng+='<div style="font-size:.78em;color:var(--danger);margin:2px 0"> 不作为主手术: '+p.c+' '+p.n+'</div>'});
		_px2.forEach(function(p){if(noPx.has(p.c))ng+='<div style="font-size:.78em;color:var(--danger);margin:2px 0"> 不作为主手术: '+p.c+' '+p.n+'</div>'});
		// Assemble final display
		var demog='';demog+='主诊:'+(pd?pd.c+' '+pd.n:'—')+' | 主手术:'+(pp?pp.c+' '+pp.n:'—');
		demog+=' | 其他诊:'+_dx2.length+' | 其他手术:'+_px2.length;
		if(_gdr)demog+=' | 性别:'+(_gdr==='M'?'男':'女');
		var ageSpan=document.getElementById('age-disp');if(ageSpan&&ageSpan.textContent)demog+=' | 年龄:'+ageSpan.textContent.replace(/\s*\d+天$/,'');
		if(gdrNote)demog+=' <span style="color:var(--accent)">('+gdrNote+')</span>';
		document.getElementById('qy-warn').innerHTML='';
		var isLF=document.getElementById('drg-ver').value==='linfen';
		document.getElementById('drr').innerHTML='<div class="clr">'+titleHTML+'<div style="font-size:.82em;color:var(--text-dim);margin:8px 0 12px 0;padding:6px 10px;background:var(--bg);border-radius:6px">'+demog+'</div>'+ng+drgHTML+'<div style="font-size:.72em;color:var(--text-dim);margin-top:12px;padding-top:8px;border-top:1px dotted var(--border)">按CHS-DRG 2.0分组方案规则引擎 | 优先级: 先期分组(MDCA) → 外科部分 → 非手术室操作 → 内科部分 → QY歧义处理</div>'+(isLF?'<div style="font-size:.72em;color:var(--text-dim);margin-top:8px;padding-top:6px;border-top:1px dotted var(--border)"><b>山西临汾 CHS-DRG-SX2026</b> | 753组 | 基准费率 4,676.74 元/权重 | 2026版权重调整: 产科+18.5% 精神科+15.8% 耳鼻口咽+15.4% 烧伤-10.2% | 机构系数: 三级1.0 二级0.8 一级0.6（当前已选等级自动计入）</div>':'')+'</div></div>'
}// DRG

var _mccCrit={
'A41.900':['A40-A41','脓毒症','发热>38℃或<36℃,寒战,意识改变','WBC>12或<4×10⁹/L,CRP/PCT↑,血培养(+)','CT/超声示感染源','','Sepsis-3: SOFA≥2分; qSOFA≥2项(RR≥22,SBP≤100,GCS<15) | 参考文献: 脓毒性休克血流氧流分型与临床管理专家共识(2025,北京协和医院)32条推荐; 1h:血培养+广谱抗生素+补液+乳酸监测'],
'R57.200':['R57','休克','低血压,肢端冷,少尿<0.5mL/kg/h','血乳酸>2mmol/L','','','脓毒症+充分液体复苏后仍需升压药维持MAP≥65mmHg+乳酸>2mmol/L | 参考文献: 脓毒性休克血流氧流共识(2025):血压非目标,灌注才是;血流与氧流[两手抓];微循环+线粒体为氧流[最后一公里]'],
'R65.100':['R65','SIRS','T>38℃或<36℃,HR>90,RR>20','WBC>12或<4×10⁹/L或幼稚>10%','','','SIRS≥2项;若同时感染→脓毒症(SOFA≥2);重症SIRS伴器官功能不全=MCC | 参考文献: Sepsis-3定义(2016); 中国脓毒症急诊指南(2025):1h急救包'],
'R65.300':['R65','MODS','SOFA评分≥2个器官各≥2分; ≥3个器官衰竭→死亡率>80% | 参考文献: 脓毒性休克共识(2025):6维SOFA评估(呼吸/凝血/肝/循环/神经/肾)','SOFA评分≥2个器官各≥2分','','','呼吸/凝血/肝/循环/神经/肾≥3个衰竭→死亡率>80%'],
'R40.200':['R40','昏迷','GCS≤8,无睁眼/言语/运动反应','','CT/MRI排查病因(卒中/外伤/感染)','','GCS≤8→深昏迷需气管插管 | 参考文献: 中国重症卒中管理指南(2024):NIHSS≥15或GCS≤12=重症;大面积(DWI>145ml或CT>1/2MCA)→去骨瓣减压;脑出血:幕上>30ml/幕下>10ml→MCC;血糖7.8-10'],
'G93.500':['G93','脑疝','瞳孔散大固定+去脑强直+Cushing反应','','CT/MRI示脑组织移位/脑池消失','','瞳孔散大固定+去脑强直+Cushing反应;CT示脑组织移位/脑池消失。紧急手术 | 参考文献: 中国重症卒中指南(2024):甘露醇/高张盐水降颅压;60岁以下恶性MCA→去骨瓣减压'],
'G41.900':['G41','癫痫持续状态','抽搐>5min或≥2次发作间意识不恢复','监测AED血药浓度','EEG:持续性痫样放电','','抽搐>5min或≥2次意识不恢复。难治性:一线(苯二氮卓)+二线(丙戊酸/左乙拉西坦)无效→麻醉剂+EEG。死亡率10-20% | 参考文献: 中国重症卒中指南(2024);ILAE癫痫持续状态指南'],
'G61.000':['G61','吉兰-巴雷综合征','对称性肢体无力(下肢→上肢)+脑神经受累','CSF蛋白-细胞分离(蛋白↑+WBC正常)','','','对称性无力(下肢→上肢)+脑神经+腱反射消失+CSF蛋白-细胞分离。重症:FVC<20mL/kg→机械通气+PE/IVIG | 参考文献: 中国GBS诊治指南;EAN/PNS GBS指南(2023)'],
'G70.000':['G70','重症肌无力危象','球麻痹+呼吸肌无力+CO₂潴留','','','','肌无力突然加重(球麻痹/呼吸肌无力)→FVC下降→气管插管。诱因:感染/药物/手术。需PE/IVIG+激素 | 参考文献: 中国重症肌无力诊治指南;MGFA危象管理共识'],
'J80.x00':['J80','ARDS','急性呼吸困难,发绀,双肺湿啰音','PaO₂/FiO₂(轻200-300/中100-200/重<100)','胸片/CT:双肺浸润影(非心源性)','','柏林定义:起病<1周+双肺浸润+非心源性; P/F:轻200-300/中100-200/重<100(死亡率>45%) | 参考文献: 中国成人ARDS指南(2023,首部GRADE方法):激素24h内启用;俯卧位≥12h/天; ARDS精准分型共识(2025):炎症亚型/呼吸生理/影像组学多维度分型'],
'J96.000':['J96','急性呼吸衰竭','呼吸困难,发绀,辅助呼吸肌参与','PaO₂<60(Ⅰ型)或PaO₂<60+PaCO₂>50(Ⅱ型)','','','Ⅰ型(PaO₂<60+PaCO₂正常/↓); Ⅱ型(PaO₂<60+PaCO₂>50+pH<7.35急性失代偿)。pH<7.25→紧急插管;需机械通气>24h=MCC | 参考文献: 中国ARDS指南(2023):拔管后推荐HFNO优于传统氧疗'],
'J93.000':['J93','张力性气胸','气管偏移,患侧呼吸音消失,颈静脉怒张','','不需影像确诊即可穿刺减压','','气管偏移+患侧呼吸音消失+颈静脉怒张+低血压→不需影像确诊即行紧急穿刺(第2肋间锁骨中线)→胸管引流 | 参考文献: 英国胸科学会BTS气胸指南;创伤失血性休克共识(2023)'],
'J86.900':['J86','脓胸','发热,胸痛,呼吸困难','胸水pH<7.2+葡萄糖<2.2mmol/L+LDH>1000','超声/CT:包裹性积液/分隔','','需胸腔引流(>24F)+纤溶剂/VATS手术'],
'Z99.100':['Z99','呼吸机依赖','长期机械通气>21天,SBT反复失败','','','','需气管切开+康复;常因COPD/神经肌肉疾病/膈肌功能障碍'],
'I21.900':['I20-I25','急性心肌梗死','胸痛>20min,放射至左臂/下颌,伴出汗恶心','hs-cTn↑>99百分位;CK-MB↑','ECG:ST段抬高/新LBBB;超声:节段性室壁运动异常','冠脉血栓/斑块破裂','第4版全球定义:hs-cTn↑>99百分位URL+胸痛/ECG缺血改变/新发心肌失活/血栓。STEMI:紧急PCI(FMC至球囊≤90min);延迟>120min→溶栓后PCI | 参考文献: 中国NSTE-ACS指南(2024)114条推荐,0h/1h hs-cTn方案;中国STEMI指南(2024):DAPT≥12月(替格瑞洛/普拉格雷优先)'],
'I22.900':['I20-I25','再发心肌梗死','胸痛+既往28d内心梗史','hs-cTn再次升高(>20%基础值)','ECG:新发改变','新发血栓','hs-cTn再次升高>20%基础值+新发ECG改变/影像证据,与首次AMI区分 | 参考文献: 中国NSTE-ACS指南(2024)'],
'R57.000':['R57','心源性休克','SBP<90mmHg>30min,肢冷,少尿,意识改变','CI<2.2L/min/m²,PCWP>15mmHg','超声:LVEF<40%,心输出量↓','','SBP<90mmHg>30min或需升压药+末梢灌注不足+CI<2.2+PCWP>15mmHg。AMI后最常见,死亡率>50% | 参考文献: 中国心衰指南(2024):湿冷型(SBP<90)首选正性肌力药,无效用去甲肾上腺素;机械支持(IABP/ECMO/LVAD)'],
'I46.000':['I46','心脏骤停(成功复苏)','意识丧失+无脉搏+无有效呼吸','','ECG:室颤/无脉室速/心室停搏/PEA','','CPR+除颤(双相200J)+肾上腺素(1mg/3-5min)+亚低温(32-36°C×24h);ROSC后记录 | 参考文献: 中国心肺复苏指南;AHA/ESC指南'],
'I49.000':['I49','室颤/室扑','意识丧失,无脉搏','','ECG:不规则宽QRS,无有效收缩','','需立即除颤(双相200J);属MCC'],
'I71.000':['I71','主动脉夹层','撕裂样胸背痛,双上肢血压差>20mmHg','','CTA/TEE:内膜片+真/假腔','中膜变性/囊性坏死','撕裂样胸背痛+双上肢血压差>20mmHg+主动脉瓣反流。CTA/TEE:内膜片+真/假腔。A型→紧急手术(48h死亡率>50%);B型→血压控制(SBP<120) | 参考文献: ESC主动脉疾病指南;中国主动脉夹层诊疗规范'],
'I26.900':['I26','肺栓塞(大面积)','突发胸痛,呼吸困难,咯血','D-二聚体↑;肌钙蛋白↑(右室损伤)','CTPA:充盈缺损;超声:McConnell征,RV/LV>1','','大面积(高危)PE:sBP<90>15min或需升压药+CTPA充盈缺损+右室功能障碍(McConnell征,RV/LV>1)+肌钙蛋白↑。溶栓/导管介入,死亡率>30% | 参考文献: ESC急性肺栓塞指南;中国肺栓塞诊治指南'],
'I50.100':['I50','急性左心衰竭','端坐呼吸,咳粉红泡沫痰,双肺湿啰音','BNP/NT-proBNP↑','胸片:肺水肿,心影增大','','Killip≥III级(肺水肿)/IV级(心源性休克)。4分型:干暖/干冷/湿暖(血管型→血管扩张药,心脏型→利尿剂)/湿冷(SBP<90→正性肌力药)。住院病死率~12%,1年再住院率45% | 参考文献: 中国心力衰竭诊断和治疗指南(2024,张抒扬/韩雅玲):分型导向个体化治疗;国家心衰指南(2023):首提[易损期]概念'],
'I31.900':['I31','心脏压塞','Beck三联征:低血压+颈静脉怒张+心音低钝','','超声:心包积液+右房/室舒张期塌陷','','Beck三联征(低血压+颈静脉怒张+心音低钝)+超声(右房/室塌陷)+奇脉(SBP吸气↓>10mmHg)。紧急心包穿刺 | 参考文献: ESC心包疾病指南;中国心衰指南(2024)'],
'A40.900':['A40-A41','链球菌性脓毒症','同A41.900标准','血培养链球菌(+)','','','参见A41.900脓毒症标准'],
'E11.000':['E10-E14','糖尿病酮症酸中毒(DKA)','多饮多尿,恶心呕吐,呼吸深快(Kussmaul),意识障碍','血糖>13.9;酮体≥++;pH<7.3;HCO₃⁻<15','','','血糖>13.9+酮体≥++pH<7.3+HCO₃⁻<18+AG>12。重度:pH<7.0或HCO₃⁻<5→MCC,死亡率>5% | 参考文献: ISPAD 2022/儿童DKA指南(2024):0.9%NaCl+胰岛素0.1U/kg/h+K⁺<5.3时补钾;pH<6.9可补碱;中国高血糖危象指南:血酮≥3mmol/L诊断'],
'E11.100':['E10-E14','高渗性高血糖状态(HHS)','严重脱水,意识障碍(昏睡→昏迷),无明显酮症','血糖>33.3;渗透压>320mOsm/L;pH>7.3','','','血糖>33.3+渗透压>320+意识障碍+无明显酮症。渗透压=2×Na⁺+Glu+BUN。死亡率10-20%,老年HHS死亡率≈DKA的10倍 | 参考文献: 中国老年糖尿病指南(2024,第11章):补液个体化(过快→肺水肿,过慢→肾前性肾衰);SGLT2i可诱发DKA'],
'E15.x00':['E15','低血糖昏迷','意识障碍(昏迷)+Whipple三联征','血糖<2.8mmol/L','','','反复严重低血糖可致不可逆脑损伤'],
'E05.500':['E05','甲状腺危象','高热>40℃+心动过速>140+CHF+意识障碍','FT3/FT4↑,TSH↓','','','高热>40°C+HR>140+CHF+房颤+意识障碍+消化症状。Burch-Wartofsky≥45分,死亡率10-30% | 参考文献: ATA甲状腺危象指南;中国甲亢危象诊治共识:丙硫氧嘧啶+碘剂+β阻滞剂+激素+降温'],
'E27.200':['E27','肾上腺危象','低血压+低钠+高钾+低血糖','血皮质醇<3μg/dL;ACTH↑','','','紧急氢化可的松;延误可致死;诱因:感染/应激/停药'],
'E83.500':['E83','高钙血症(肿瘤性)','恶心呕吐,多尿,便秘,意识障碍(高钙危象>3.5)','校正Ca²⁺>2.75mmol/L;PTHrP↑','','','肿瘤相关(溶骨转移/PTHrP分泌);常伴AKI;需紧急降钙'],
'E87.500':['E87','高钾血症(>6.5危象)','肌无力,心悸','K⁺>6.5mmol/L','ECG:尖T→宽QRS→P波消失→正弦波','','立即静推钙剂+胰岛素+葡萄糖+利尿/透析;K⁺>6.5+ECG改变=MCC'],
'E87.100':['E87','低钠血症(重症<120)','意识障碍,抽搐,昏迷','Na⁺<120mmol/L','','','脑水肿风险;3%高渗盐水缓慢纠正(<10mmol/L/24h防ODS)'],
'N17.900':['N17','急性肾衰竭(AKI 3期)','少尿/无尿+容量超负荷(肺水肿/浮肿)','Scr≥353.6μmol/L或↑≥3倍;K⁺>6.5','超声:肾实质回声增强,排除梗阻','','KDIGO 3期:Scr≥353.6μmol/L或↑≥3倍或开始RRT或尿量<0.3mL/kg/h≥24h或无尿≥12h。紧急RRT:K⁺>6.5/pH<7.1/肺水肿/脑病/心包炎 | 参考文献: 中国AKI临床实践指南(2023,侯凡凡院士)20个临床问题;枸橼酸抗凝首选(1A);不推荐早期RRT(1B);中国住院AKI发生率2-12%,74.2%漏诊'],
'N18.500':['N18','CKD 5期(eGFR<15)','尿毒症症状:恶心呕吐/瘙痒/乏力/容量超负荷','eGFR<15mL/min/1.73m²;K⁺↑;P↑;Ca²⁺↓;Hb↓','','','eGFR<15mL/min/1.73m²(或已透析);合并症越多消耗越大 | 参考文献: 中国AKI指南(2023):等张晶体液而非胶体;血糖<10mmol/L;肾性贫血管理'],
'K72.000':['K72','急性肝功能衰竭','黄疸+肝性脑病+凝血障碍','INR≥1.5;TBil↑;ALT/AST↑↑','','','AASLD:原无肝硬化+INR≥1.5+肝性脑病+起病<26周(急性<4周/亚急性4-24周)。对乙酰氨基酚>50%,4h内NAC;死亡率>40% | 参考文献: 肝衰竭诊治指南(2024年版,李兰娟院士):新增COSSH-ACLF 1-3级;推荐Li-NBAL 3.0人工肝'],
'K74.600':['K74','肝硬化失代偿','大量腹水+黄疸+肝性脑病','ALB<28g/L;TBil>51μmol/L;INR>2.3','','','Child-Pugh C级(10-15分):大量腹水+TBil>51+ALB<28+INR>2.3+Ⅲ-Ⅳ肝性脑病。ACLF:≥1个器官衰竭→28d死亡率>30% | 参考文献: 肝衰竭指南(2024):COSSH-ACLF分级;肠道微生态+粪菌移植新增'],
'I85.000':['I85','食管静脉曲张破裂出血','呕血,黑便,血流动力学不稳定','Hb↓;PLT↓(脾亢)','内镜:曲张静脉破裂出血(喷射/渗血/血栓头)','','紧急内镜套扎+特利加压素+抗生素;再出血率>30%(7d内)'],
'K85.900':['K85','急性胰腺炎(重症坏死性)','剧烈上腹痛(放射至背)+腹胀+发热','淀粉酶/脂肪酶↑>3倍;Ca²⁺<2.0;血糖>11.1','CT:胰腺坏死>30%+胰周积液/感染性坏死','','Ranson≥3/APACHE-II≥8;CT:胰腺坏死>30%+感染性坏死→MCC,死亡率>30% | 参考文献: 急性胰腺炎急诊诊治专家共识(2024,中华医学会急诊医学分会):急性反应期(72h)目标化管理;限制性液体复苏+阻断SIRS+肠道功能保护'],
'K65.000':['K65','急性弥漫性腹膜炎','腹膜刺激征(压痛反跳痛肌紧张)+肠梗阻(肠音消失)','WBC↑;CRP↑;PCT↑','CT:游离气体/腹腔积液','','消化道穿孔→紧急剖腹;Mannheim腹膜炎指数>26→MCC'],
'D65.x00':['D65','DIC','出血(皮肤瘀斑/穿刺点/黏膜)+血栓(肢端缺血)','PLT↓;PT↑;FDP/D-二聚体↑↑;纤维蛋白原<1g/L','','','ISTH显性DIC评分≥5:PLT(>100=0/50-100=1/<50=2)+D-二聚体/FDP(中度↑=2/显著↑=3)+PT延长(<3s=0/3-6s=1/>6s=2)+Fib(>1g/L=0/≤1g/L=1)。出血+血栓并存,死亡率30-50% | 参考文献: 脓毒症性凝血病诊疗中国专家共识(2024):中国SIC标准PLT<100(vs ISTH<150);[三抗一防];产科DIC共识(2023):CDSS>7诊断,原发病治疗紧迫'],
'D70.x00':['D70','粒细胞缺乏症','发热>38.3℃(粒缺发热)','ANC<0.5×10⁹/L(<0.1为极重度)','','','ANC<0.5(<0.1极重度)。粒缺发热(单次≥38.3°C或持续≥38°C>1h)→1h内启动广谱抗生素。化疗后/药物反应,感染死亡率10-30% | 参考文献: NCCN/中国粒缺发热管理指南;MASCC风险评分指导门诊/住院'],
'D61.900':['D61','再生障碍性贫血(重型)','贫血(乏力气短)+出血(PLT↓)+感染(ANC↓)','ANC<0.5;PLT<20;网织红<20×10⁹/L','骨髓:有核细胞<25%','','骨髓有核细胞<25%+外周血≥2项(ANC<0.5/PLT<20/网织红<20)。需ATG+CsA或HSCT,未经治疗死亡率>80%(<6月) | 参考文献: 中国AA诊治指南;EBMT AA指南'],
'D59.300':['D59','溶血性尿毒症综合征(HUS)','腹泻(血便)+少尿','微血管病溶血(Hb↓+裂红细胞+LDH↑)+PLT↓+AKI','','','典型HUS:大肠杆菌O157:H7;需血浆置换/透析'],
'M31.100':['M31','血栓性血小板减少性紫癜','五联征:发热+PLT↓+神经异常+肾损害+微血管病溶血','ADAMTS13活性<10%;LDH↑;haptoglobin↓','','','死亡率>90%不治疗;需紧急血浆置换'],
'C79.300':['C79','恶性肿瘤脑转移','颅内高压(头痛呕吐视乳头水肿)+局灶神经功能缺损+癫痫','','MRI增强:多发占位+周围水肿','转移癌','大水肿+中线移位=MCC;需地塞米松+全脑放疗/SRS'],
'O15.900':['O15','子痫','高血压+蛋白尿+全身性抽搐','蛋白尿≥++或>0.3g/24h','','','子痫前期(高血压+蛋白尿)+全身抽搐→子痫。硫酸镁(负荷4-6g+维持1-2g/h)+降压+终止妊娠 | 参考文献: ACOG/中国妊娠期高血压指南;中国产科DIC共识(2023)'],
'O14.200':['O14','HELLP综合征','上腹痛+恶心呕吐+高血压','溶血(Hb↓+LDH↑)+肝酶↑(ALT>70)+PLT<100','','','溶血(Hb↓+LDH>600+裂红细胞)+肝酶↑(ALT>70)+PLT<100。Ⅰ级PLT<50(母体死亡率>40%)→MCC | 参考文献: 中国妊娠期高血压指南;ACOG HELLP管理指南'],
'O88.100':['O88','羊水栓塞','突发低氧+循环衰竭+DIC(产时/产后30min内)','凝血障碍(DIC表现)','','','突发低氧+循环衰竭+DIC(产时/产后30min内)。死亡率>60%,罕见(1/40,000) | 参考文献: 中国产科DIC共识(2023):Fib<1.5补Fib;PT/APTT>1.5倍补血浆;PLT<50+出血→补血小板'],
'P22.000':['P22','新生儿RDS','呼吸急促+鼻扇+三凹征+呻吟+需氧疗','','胸片:网格/颗粒状影+支气管充气征','','早产儿<34w;需表面活性物质+CPAP/机械通气;FiO₂>0.4=MCC'],
'P77.x00':['P77','新生儿坏死性小肠结肠炎','腹胀+喂养不耐受+血便','PLT↓;代谢性酸中毒','腹平片/超声:肠壁积气/门静脉积气/气腹','','Bell≥Ⅱb→需外科手术;Ⅲ期(穿孔+腹膜炎+休克)→MCC;死亡率20-30%'],
'P91.600':['P91','新生儿HIE(中重度)','意识障碍(嗜睡→昏迷)+惊厥+肌张力异常','','aEEG/EEG异常;MRI:基底节/分水岭损伤','','Sarnat≥Ⅱ级;需亚低温(6h内→72h);MCC级'],
'P36.900':['P36','新生儿败血症','发热/低体温+喂养困难+呼吸暂停','CRP/PCT↑;血培养(+)','','','休克(需升压药)/DIC/多器官衰竭→MCC;死亡率10-30%'],
'T79.600':['T79','骨筋膜室综合征','6P征:疼痛(被动牵拉)+苍白+无脉+感觉异常+麻痹','CK↑;肌红蛋白↑','室内压力>30mmHg或ΔP(舒张压-室内压)<30','','6P征:疼痛(被动牵拉)+苍白+无脉+感觉异常+麻痹。室内压>30mmHg或ΔP<30。紧急筋膜切开(4-6h内) | 参考文献: 创伤失血性休克共识(2023);AAOS筋膜室综合征指南'],
'T79.500':['T79','挤压综合征','肌肉长时间受压(>4h)→解除后肌红蛋白尿+AKI','CK>5000;K⁺↑;肌红蛋白↑;Scr↑','','','肌肉受压>4h→解除后肌红蛋白/CK>5000+K⁺↑+AKI。大量补液+碱化尿液+可能CRRT | 参考文献: 创伤失血性休克中国急诊专家共识(2023)35条推荐:CABCDE策略;允许性低血压(SBP80-90);大量输血1:1:1;TIC防治(氨甲环酸3h内)'],
'T79.100':['T79','脂肪栓塞综合征','呼吸困难+意识障碍+瘀点皮疹(胸/腋/结膜)','贫血+PLT↓+ESR↑','','','Gurd标准:呼吸功能不全+脑症状+瘀点皮疹。长骨/骨盆骨折后12-72h。需呼吸支持+激素 | 参考文献: 创伤失血性休克共识(2023)'],
'L89.300':['L89','Ⅳ期压疮','全层皮肤/组织缺损+骨骼/肌腱/肌肉暴露+坏死/焦痂','','','','NPUAP Ⅳ期;需清创+负压引流+皮瓣修复;合并感染/骨髓炎→MCC'],
'L51.200':['L51','TEN中毒性表皮坏死松解症','表皮剥脱>30%+黏膜广泛糜烂(口腔/眼/生殖器)+Nikolsky(+)','','','','表皮剥脱>30%+黏膜糜烂+Nikolsky(+)+发热。SCORTEN≥2。SJS<10%/TEN>30%,死亡率30-50%。停可疑药(别嘌呤醇/卡马西平/磺胺/拉莫三嗪/NSAIDs)+IVIG/环孢素/激素 | 参考文献: 中国SJS/TEN诊治专家共识;RegiSCAR评分'],
'_CHPAT':{
'A00-B99':['第1章','传染病和寄生虫病','本章MCC:严重脓毒症/感染性休克(A40-A41)、中枢神经系统感染(G00-G07)、粟粒性结核(A19)、HIV相关机会性感染(B20-B24)、感染性心内膜炎(I33)等。诊断需病原学证据+全身炎症反应+器官功能评估。'],
'C00-D49':['第2章','肿瘤','本章MCC:肿瘤溶解综合征(E88.3)、脑转移(C79.3)、上腔静脉综合征(I87.1)、脊髓压迫症(G95.8)、恶性胸腔积液(J91)、肿瘤性高钙血症(E83.5)。多为肿瘤急症,需紧急干预。'],
'D50-D89':['第3章','血液及免疫','本章MCC:DIC(D65)、粒细胞缺乏症(D70)、重型再生障碍性贫血(D61.9)、HUS(D59.3)、TTP(M31.1)、重症免疫缺陷(D80-D84)。诊断依赖外周血+骨髓+凝血功能+免疫指标。'],
'E00-E89':['第4章','内分泌/代谢','本章MCC:DKA(E10-E11)、HHS(E11)、低血糖昏迷(E15)、甲状腺危象(E05.5)、肾上腺危象(E27.2)、严重电解质紊乱(E87)、重度营养不良(E40-E46)。诊断依赖生化+激素水平+血气分析。'],
'G00-G99':['第6章','神经系统','本章MCC:昏迷(R40.2)、脑疝(G93.5)、癫痫持续状态(G41)、GBS(G61.0)、肌无力危象(G70.0)、急性脊髓炎(G37.3)、脑膜炎/脑炎(G00-G04)、重症脑卒中(I61/I63)。诊断依赖神经系统查体+CSF+EEG+影像。'],
'I00-I99':['第9章','循环系统','本章MCC:AMI(I21-I22)、心源性休克(R57.0)、心脏骤停(I46)、主动脉夹层(I71)、大面积肺栓塞(I26)、急性心衰(I50)、心脏压塞(I31.9)、高血压危象(I16)。诊断依赖ECG+肌钙蛋白+影像(CTA/TEE)+血流动力学监测。'],
'J00-J99':['第10章','呼吸系统','本章MCC:ARDS(J80)、急性呼衰(J96.0)、张力性气胸(J93)、重症肺炎(J15-J18)、脓胸(J86)、呼吸机依赖(Z99.1)。诊断依赖血气分析+胸部影像+氧合指数。'],
'K00-K95':['第11章','消化系统','本章MCC:急性肝衰(K72.0)、肝硬化失代偿(K74.6)、食管静脉曲张出血(I85.0)、重症胰腺炎(K85)、弥漫性腹膜炎(K65.0)、肝性脑病(K72.9)。诊断依赖肝功能+凝血+内镜+影像(CT/MRI)。'],
'N00-N99':['第14章','泌尿系统','本章MCC:AKI 3期(N17.9)、CKD 5期(N18.5)、梗阻性肾病(N13.8)、急进性肾炎(N01)。诊断依赖肾功能(Scr/eGFR)+尿检+超声+病理(肾穿刺)。'],
'O00-O9A':['第15章','妊娠/产褥期','本章MCC:子痫(O15)、HELLP(O14.2)、羊水栓塞(O88.1)、子宫破裂(O71.1)、产后大出血(O72)。均为产科急症,需多学科协作紧急处理,母儿死亡率高。'],
'P00-P96':['第16章','围产期','本章MCC:新生儿RDS(P22.0)、NEC(P77)、HIE(P91.6)、新生儿败血症(P36)、重度颅内出血(P10/P52)。诊断依赖临床表现+影像+血气+病原学。'],
'R00-R99':['第18章','症状/体征','本章MCC:SIRS(R65.1)、MODS(R65.3)、各型休克(R57)、昏迷(R40.2)、呼吸骤停(R09.2)、严重酸中毒(E87.2)、Ⅳ期压疮(L89.3)。作为其他诊断时参与MCC判定,注意排除规则。'],
'S00-T98':['第19章','创伤/中毒','本章MCC:挤压综合征(T79.5)、脂肪栓塞(T79.1)、骨筋膜室综合征(T79.6)、重度烧伤(T31,>20%TBSA)、中毒性表皮坏死松解症(L51.2)、创伤性休克。需紧急外科/ICU干预。'],
}
};

function _buildMcc(){
var mccS=_drg?_drg.mccS:null;
if(!mccS){document.getElementById('mcc-tb').innerHTML='<tr><td colspan="6" class="emp">DRG数据加载中...</td></tr>';return}
var all=Array.from(mccS).sort();
window._mccAll=all;
_renderMccPage(all);
}

var _clinicalNotes={
'G45.000':{n:'椎基底动脉供血不足(后循环TIA)',s:'眩晕(47%)+复视+构音障碍+共济失调+双侧/交叉性感觉运动障碍+跌倒发作+TGA',i:'MRI+DWI(金标准,排除梗死);CTA/MRA;TCD',r:'后循环TIA:24h内症状完全恢复+DWI无梗死灶。孤立性眩晕极少是PCI,须合并其他脑干/小脑体征。ABCD²评分对后循环TIA预测价值有限,建议常规CTA/MRA。|参考文献:中国后循环缺血专家共识(2006);中国急性缺血性脑卒中诊治指南(2023);中国脑血管病临床管理指南(2023);NEJM后循环综述(2023)'},
'G45.001':{n:'椎动脉综合征(Wallenberg)',s:'眩晕+复视+同侧Horner+对侧痛温觉障碍+小脑性共济失调',i:'MRI+DWI;CTA/MRA示椎动脉狭窄/闭塞;DSA金标准',r:'同侧Horner+同侧面部痛温觉↓+对侧肢体痛温觉↓+眩晕/恶心/眼震+构音障碍/吞咽困难+同侧小脑共济失调。最常见病因:椎动脉夹层/动脉粥样硬化。|参考文献:后循环缺血专家共识(2006)'},
'G45.002':{n:'基底动脉综合征(基底动脉尖)',s:'意识障碍+四肢瘫+瞳孔异常+眼动障碍+去脑强直',i:'MRI+DWI;CTA/MRA示基底动脉狭窄/闭塞;DSA可同时介入',r:'基底动脉尖=双侧丘脑+中脑+枕叶+颞叶内侧→意识障碍/垂直凝视麻痹/皮质盲/Korsakoff样遗忘。基底动脉闭塞自然病程死亡率>80%,需积极再通。|参考文献:中国脑血管病临床管理指南(2023);NEJM后循环综述(2023)'},
'G45.900':{n:'短暂性脑缺血发作(后循环)',s:'眩晕+复视+构音障碍+共济失调+双侧/交叉性感觉运动障碍+视野缺损',i:'MRI+DWI(必须无梗死灶);CTA/MRA评估血管',r:'后循环TIA卒中复发风险与前循环无显著差异。双抗:轻型TIA(NIHSS≤3),24h内阿司匹林+氯吡格雷,21天后改单抗。鉴别:BPPV/梅尼埃病/前庭神经炎/前庭性偏头痛。|参考文献:中国急性缺血性脑卒中指南(2023)'},
'I63.900':{n:'脑梗死(急性缺血性脑卒中)',s:'突发局灶性神经功能缺损:偏瘫+偏身感觉障碍+偏盲+失语+构音障碍+眩晕/共济失调(后循环)',l:'血糖(排除低血糖)+凝血功能',i:'CT平扫(排除出血);MRI+DWI(金标准,敏感性>95%);CTA/MRA评估大血管闭塞',r:'急性期:①溶栓(阿替普酶0.9mg/kg,≤4.5h,后循环可延至6-9h);②取栓(大血管闭塞,≤24h);③双抗(轻型NIHSS≤3);④他汀强化。后循环梗死出血风险不高于前循环。|参考文献:中国急性缺血性脑卒中诊治指南(2023);中国脑血管病临床管理指南(2023)'},
'I65.001':{n:'椎动脉闭塞/狭窄',s:'眩晕+脑干/小脑缺血+TIA/卒中发作',l:'血脂+血糖+HbA1c',i:'CTA/MRA示椎动脉狭窄;DSA金标准',r:'动脉粥样硬化(45%)+夹层(年轻患者)。狭窄>50%有临床意义。治疗:抗血小板+他汀强化+危险因素控制。|参考文献:中国脑血管病临床管理指南(2023)'},
'I65.101':{n:'基底动脉闭塞/狭窄',s:'意识障碍+四肢瘫+瞳孔异常+眼动障碍+后循环TIA/卒中',l:'血脂+血糖+HbA1c',i:'CTA/MRA/DSA示基底动脉狭窄/闭塞',r:'基底动脉闭塞为最严重缺血性卒中类型,未经治疗死亡率>80%。|参考文献:中国脑血管病临床管理指南(2023)'},
'I63.901':{n:'脑干梗死',s:'复视+眩晕+构音障碍+吞咽困难+交叉性瘫+共济失调+Horner征',i:'MRI+DWI(必须,CT假阴性率高);CTA/MRA评估椎基底动脉',r:'脑干梗死症状复杂:延髓(Wallenberg)/脑桥(Millard-Gubler/Foville)/中脑(Weber/Benedikt)。后循环可适当延长溶栓时间窗。|参考文献:后循环缺血专家共识(2006)'},
'I63.902':{n:'小脑梗死',s:'眩晕+恶心呕吐+共济失调+眼球震颤+头痛',i:'MRI+DWI确诊;CT早期可正常',r:'小脑梗死占全部脑梗死3%。警惕:小脑水肿→梗阻性脑积水→脑干受压→枕骨大孔疝。大面积(>1/3小脑半球)→去骨瓣减压。|参考文献:中国脑血管病临床管理指南(2023)'},
'G46.300':{n:'小脑后下动脉综合征(Wallenberg)',s:'同侧Horner+同侧面部痛温觉↓+对侧肢体痛温觉↓+眩晕/恶心/眼震+构音障碍/吞咽困难+同侧小脑共济失调',i:'MRI+DWI示延髓背外侧梗死;CTA/MRA示椎动脉/PICA病变',r:'后循环梗死最常见类型(占36%)。最常见病因:椎动脉/PICA动脉粥样硬化/夹层。预后较好:多数恢复独立行走。|参考文献:后循环缺血专家共识(2006)'},
	'K59.000':{n:'便秘(功能性/器质性/继发性)',s:'罗马IV标准(≥6月,近3月符合≥2项):①排便费力≥25% ②块状/硬便(Bristol 1-2型)≥25% ③排便不尽感≥25% ④肛门直肠梗阻/堵塞感≥25% ⑤手法辅助排便≥25% ⑥自发排便<3次/周。附加:不用泻药时很少稀便,不符合IBS标准',l:'血常规+血糖+甲功(TSH/FT4排除甲减)+电解质(Ca²⁺)+肿瘤标志物(年龄>45或报警症状)',i:'结肠镜(年龄≥45或有报警症状:便血/消瘦/贫血);肛门直肠测压(出口梗阻型);结肠传输试验(慢传输型);排粪造影(直肠前突/套叠)',r:'分型:慢传输型/出口梗阻型/混合型。治疗:①容积性泻药(欧车前)②渗透性泻药(乳果糖/PEG)③刺激性泻药(比沙可啶,短期)④促动力药(普芦卡必利)⑤微生态制剂⑥生物反馈(出口梗阻型)。|审核要点:MCC编码需独立评估处理记录(排便频率/Bristol分型/处理措施),如为其他疾病伴随症状不应单独编码。医保飞检重点:高套MCC风险。|参考文献:罗马IV功能性胃肠病标准(2016);中国慢性便秘诊治指南(2019);中国功能性便秘专家共识(2020)'},
};

function _mccCriteria(code){
if(_mccCrit[code])return _mccCrit[code];
if(_mccCrit[code+'00'])return _mccCrit[code+'00'];
if(_mccCrit[code+'000'])return _mccCrit[code+'000'];
var m=code.match(/^([A-Z]\d+)\./);
if(m){
var pfx=m[1]+'.x00'; if(_mccCrit[pfx])return _mccCrit[pfx];
var rng=m[1][0]; for(var k in _mccCrit._CHPAT){
var parts=k.split('-'); if(rng>=parts[0]&&rng<=parts[1])return ['','',_mccCrit._CHPAT[k][2],'','','',_mccCrit._CHPAT[k][1]+' MCC'];
}
for(var k in _mccCrit){if(k[0]===m[1][0]&&k.indexOf('.')>0){var mc=k.match(/^([A-Z]\d+)\./);if(mc&&mc[1]===m[1])return _mccCrit[k]}}
}
return null;
}

function _renderMccPage(list){
var total=list.length;
var page=window._mccPage||0;
var ps=100;
var start=page*ps;
var end=Math.min(start+ps,total);
var show=list.slice(start,end);
var info=document.getElementById('mcc-info');
var q=document.getElementById('mcc-q').value.trim();
if(q)info.textContent='搜索 "'+q+'" 匹配 '+total+' 条MCC编码';
else info.textContent='共 '+total.toLocaleString()+' 条MCC严重合并症/并发症编码 (CHS-DRG 2.0)';
var h='';
for(var i=0;i<show.length;i++){
var code=show[i];
var name=(D&&D.m10&&D.m10[code])?D.m10[code].n:'';
// Subcategory: prefer _drg.mcc_hier (from ICD-10 DB), fallback to _mccCrit
var hier=(_drg&&_drg.mcc_hier&&_drg.mcc_hier[code])?_drg.mcc_hier[code]:null;
var cr=_mccCriteria(code);
var sub=hier?hier[0]:(cr?cr[0]:'');
var subn=hier?hier[1]:(cr?cr[1]:'');
var sx='',lab='',img='',path='',note='';
if(cr){
if(cr[2]||cr[3]||cr[4]||cr[5]){
sx=cr[2]?'<b>症状:</b> '+cr[2]+'<br>':'';
lab=cr[3]?'<b>检验:</b> '+cr[3]+'<br>':'';
img=cr[4]?'<b>检查:</b> '+cr[4]+'<br>':'';
path=cr[5]?'<b>病理:</b> '+cr[5]+'<br>':'';
}
note=cr[6]||'';
}
var crid='mcr'+code.replace(/[^a-zA-Z0-9]/g,'_');
var critFull=(sx||lab||img||path)?(sx+lab+img+path):(note||'');
var critShort=critFull.replace(/<[^>]+>/g,'').substring(0,80)+(critFull.length>80?'...':'');
h+='<tr id="'+crid+'" onclick="_mccExpand(\''+crid+'\',\''+code.replace(/'/g,'')+'\')">';
h+='<td><span class="tag" style="color:var(--danger);font-weight:600">'+code+'</span></td>';
h+='<td>'+name+'</td>';
h+='<td style="font-size:.82em">'+(sub?'<span class="tag ts">'+sub+'</span>':'—')+'</td>';
h+='<td style="font-size:.82em">'+(subn||'—')+'</td>';
h+='<td style="font-size:.78em;max-width:300px">'+critShort+'</td>';
h+='<td style="font-size:.75em;color:var(--text-dim)">'+note.substring(0,40)+(note.length>40?'…':'')+'</td>';
h+='</tr>';
h+='<tr id="h_'+crid+'" style="display:none;background:var(--bg-input)"><td colspan="6" id="hc_'+crid+'"></td></tr>';
}
document.getElementById('mcc-tb').innerHTML=h||'<tr><td colspan="6" class="emp">未找到匹配的MCC编码</td></tr>';
// Pagination
var pghtml='';
var totalPages=Math.ceil(total/ps);
if(totalPages>1){
pghtml='<span style="margin-right:12px">第'+(page+1)+'/'+totalPages+'页</span>';
if(page>0)pghtml+='<button onclick="_mccGo('+(page-1)+')" style="margin:0 4px;padding:3px 10px;border:1px solid var(--border);background:var(--bg-card);border-radius:var(--r-xs);cursor:pointer;font-size:.82em">← 上一页</button>';
if(page<totalPages-1)pghtml+='<button onclick="_mccGo('+(page+1)+')" style="margin:0 4px;padding:3px 10px;border:1px solid var(--border);background:var(--bg-card);border-radius:var(--r-xs);cursor:pointer;font-size:.82em">下一页 →</button>';
}
document.getElementById('mcc-page').innerHTML=pghtml;
}

function _mccGo(p){window._mccPage=p;_renderMccPage(window._mccAll)}
function _searchMcc(){
var q=document.getElementById('mcc-q').value.trim().toLowerCase();
window._mccPage=0;
if(!window._mccAll||!_drg){document.getElementById('mcc-tb').innerHTML='<tr><td colspan="6" class="emp">DRG数据加载中，请稍候...</td></tr>';return}
var all=window._mccAll;
if(q){
var m=D?D.m10:null;
all=all.filter(function(c){
if(c.toLowerCase().indexOf(q)>=0)return true;
if(m&&m[c]&&m[c].n.toLowerCase().indexOf(q)>=0)return true;
var cr=_mccCriteria(c);
if(cr){
for(var i=0;i<cr.length;i++){if(cr[i]&&cr[i].toLowerCase().indexOf(q)>=0)return true}
}
return false;
});
}
_renderMccPage(all);
}

function _mccExpand(rid,code){
var nr=document.getElementById('h_'+rid);
if(!nr)return;
if(nr.style.display==='none'){
nr.style.display='';
var hier=(_drg&&_drg.mcc_hier&&_drg.mcc_hier[code])?_drg.mcc_hier[code]:null;
var cr=_mccCriteria(code);
var name=(D&&D.m10&&D.m10[code])?D.m10[code].n:'';
var hc=document.getElementById('hc_'+rid);
var h='<div style="padding:8px 16px;font-size:.78em;line-height:1.7">';
if(hier||cr){
var esub=hier?hier[0]:(cr?cr[0]:'');
var esubn=hier?hier[1]:(cr?cr[1]:'');
h+='<div style="margin-bottom:6px"><b style="color:var(--danger)">'+code+'</b> '+name+'</div>';
if(esub)h+='<div><b>亚目:</b> '+esub+' '+esubn+'</div>';
if(cr[2])h+='<div style="margin-top:4px"><b>🩺 症状:</b> '+cr[2]+'</div>';
if(cr[3])h+='<div><b>🧪 检验:</b> '+cr[3]+'</div>';
if(cr[4])h+='<div><b>📋 检查:</b> '+cr[4]+'</div>';
if(cr[5])h+='<div><b>🔬 病理:</b> '+cr[5]+'</div>';
if(cr[6])h+='<div style="margin-top:4px;padding:4px 8px;background:rgba(232,85,85,.06);border-left:3px solid var(--danger);border-radius:0 4px 4px 0"><b>备注:</b> '+cr[6]+'</div>';
}else{
h+='<div><b>'+code+'</b> '+name+'</div>';
h+='<div style="color:var(--text-dim)">该编码为CHS-DRG 2.0收录MCC，详细诊断标准待补充</div>';
}
h+='</div>';
hc.innerHTML=h;
}else nr.style.display='none';
}

// Lazy init: build MCC table when details opened
document.getElementById('mcc-ref').addEventListener('toggle',function(){
if(this.open&&(!window._mccAll))_buildMcc();
});



// ═══ Batch DRG Analysis ═══
function _computeOneDrg(pd, dx2codes, pp, px2codes, gender) {
    if (!_drg) return {error: 'DRG数据未加载'};
    function _lookDx(code) {
        var m = _drg.dx2a[code];
        if (m) return m;
        var b = code.match(/^([A-Z]\d{2}\.\d+)/);
        if (b) { var k = b[1] + 'x001'; m = _drg.dx2a[k]; if (m) return m;
            m = _drg.dx2a[b[1]]; if (m) return m; }
        m = _drg.dx2a[code + 'x001'];
        return m || [];
    }
    function _lookPx(code) {
        var m = _drg.px2a[code];
        if (m) return m;
        if (code.indexOf('.') > 0) { var p = code.split('.'); var base = p[0] + '.' + p[1].substring(0, 2); m = _drg.px2a[base]; }
        return m || [];
    }
    function _filterGender(k) {
        if (gender === 'M' && 'NO'.indexOf(k[0]) >= 0) return true;
        if (gender === 'F' && k[0] === 'M') return true;
        return false;
    }
    var dxMDC = '', pxMDC = '';
    if (pd) { var dm = _lookDx(pd.c); if (dm.length > 0) dxMDC = dm[0].a[0]; }
    if (pp) { var pm = _lookPx(pp.c); if (pm.length > 0) pxMDC = pm[0].a[0]; }
    var isQY = !!(dxMDC && pxMDC && dxMDC !== pxMDC);
    var byMDC = {};
    function _addToMDC(mdc, cat, adrg, info, matchedBy) {
        var key = mdc + '|' + cat;
        if (!byMDC[key]) byMDC[key] = {mdc: mdc, cat: cat, adrgs: {}};
        var a = byMDC[key].adrgs;
        if (!a[adrg]) a[adrg] = {an: info.an, drgs: info.d || [], matched: []};
        if (a[adrg].matched.indexOf(matchedBy) < 0) a[adrg].matched.push(matchedBy);
    }
    var entries = [];
    if (pd) entries.push(['P', pd, 'dx']);
    dx2codes.forEach(function(d) { if (d) entries.push(['S', d, 'dx']); });
    if (pp) entries.push(['Px', pp, 'px']);
    px2codes.forEach(function(p) { if (p) entries.push(['s', p, 'px']); });
    entries.forEach(function(x) {
        var d = x[1]; if (!d) return;
        var matches = x[2] === 'dx' ? _lookDx(d.c) : _lookPx(d.c);
        matches.forEach(function(a) {
            var k = a.a; if (_filterGender(k)) return;
            var md = _drg.adrg_mdc[k] || {};
            var mdc = md.mdc || k[0];
            var cat = md.cat || '';
            var c = cat.indexOf('外科') >= 0 ? 'S' : (cat.indexOf('操作') >= 0 || cat.indexOf('手术室') >= 0 ? 'P' : 'M');
            _addToMDC(mdc, c, k, a, x[0] === 'P' ? '主诊:' + d.c : (x[0] === 'S' ? '其他诊:' + d.c : (x[0] === 'Px' ? '主手术:' + d.c : '其他手术:' + d.c)));
        });
    });
    function _pickBest(mdcToCheck) {
        var cats = ['MDC' + mdcToCheck + '|S', 'MDC' + mdcToCheck + '|P', 'MDC' + mdcToCheck + '|M'];
        for (var ci = 0; ci < cats.length; ci++) {
            var entry = byMDC[cats[ci]];
            if (!entry) continue;
            var result = {mdc: entry.mdc, cat: entry.cat === 'S' ? '外科部分' : (entry.cat === 'P' ? '非手术室操作部分' : '内科部分'), adrgs: [], primary: null};
            for (var ak in entry.adrgs) {
                var a = entry.adrgs[ak];
                var hasPD = pd && _lookDx(pd.c).some(function(x) { return x.a === ak; });
                var hasPP = pp && _lookPx(pp.c).some(function(x) { return x.a === ak; });
                result.adrgs.push({code: ak, name: a.an, drgs: a.drgs, matched: a.matched, hasPD: hasPD, hasPP: hasPP});
            }
            result.adrgs.sort(function(a, b) { var sa = (a.hasPP ? 2 : 0) + (a.hasPD ? 1 : 0); var sb = (b.hasPP ? 2 : 0) + (b.hasPD ? 1 : 0); return sb - sa; });
            if (result.adrgs.length > 0) { result.primary = result.adrgs[0]; return result; }
        }
        return null;
    }
    var decision = _pickBest(dxMDC);
    var decisionNote = '';
    if (!decision && isQY && pxMDC) { decision = _pickBest(pxMDC); if (decision) decisionNote = '手术优先'; }
    if (!decision && isQY) { decision = _pickBest(dxMDC); if (decision) decisionNote = '诊断路径'; }
    var mccInfo = {mccDx: [], ccDx: [], exDx: [], effS: 'noCC'};
    if (decision && decision.primary && pd) {
        var primAdrg = decision.primary;
        var mccS = _drg.mccS || new Set, ccS = _drg.ccS || new Set;
        var mccT = _drg.mccT || {}, ccT = _drg.ccT || {}, excl = _drg.excl || {};
        dx2codes.forEach(function(d) {
            if (!d) return;
            if (mccS.has(d.c)) { var tbl = mccT[d.c] || '', exclCodes = excl[tbl] || []; if (exclCodes.indexOf(pd.c) < 0) mccInfo.mccDx.push(d.c); else mccInfo.exDx.push(d.c); }
            else if (ccS.has(d.c)) { var tbl2 = ccT[d.c] || '', exclCodes2 = excl[tbl2] || []; if (exclCodes2.indexOf(pd.c) < 0) mccInfo.ccDx.push(d.c); else mccInfo.exDx.push(d.c); }
        });
        mccInfo.effS = mccInfo.mccDx.length > 0 ? 'MCC' : (mccInfo.ccDx.length > 0 ? 'CC' : 'noCC');
        var drgs = primAdrg.drgs || []; var finalD = drgs[0];
        for (var j = 0; j < drgs.length; j++) { if (drgs[j].s === mccInfo.effS) { finalD = drgs[j]; break; } }
        primAdrg.finalDRG = finalD || drgs[0];
    }
    return {decision: decision, mccInfo: mccInfo, isQY: isQY, dxMDC: dxMDC, pxMDC: pxMDC, decisionNote: decisionNote};
}
function _detectCols(headers) {
    var r = {dxCode: -1, dxName: -1, dx2Cols: [], pxCode: -1, pxName: -1, px2Cols: [], gender: -1, age: -1};
    var pat = {
        dxCode: [/主要诊断编码|主诊断编码|主要诊断代码|主诊断代码|出院.*主要诊断.*编码|出院诊断编码/],
        dxName: [/主要诊断名称|主诊断名称|出院.*主要诊断.*名称|出院诊断名称/],
        dx2: [/其他诊断编码|次要诊断编码|合并症.*编码|并发症.*编码|其他诊断|次要诊断/],
        pxCode: [/主要手术编码|主手术编码|主要操作编码|出院.*主要手术.*编码|手术编码/],
        pxName: [/主要手术名称|主手术名称|主要操作名称|手术名称/],
        px2: [/其他手术编码|次要手术编码|其他操作编码|其他手术|次要手术/],
        gender: [/^性别$|^患者性别/],
        age: [/^年龄$|^患者年龄|^岁数|^实足年龄/]
    };
    headers.forEach(function(h, i) {
        for (var k in pat) for (var j = 0; j < pat[k].length; j++) {
            if (pat[k][j].test(h)) { if (k === 'dx2' || k === 'px2') r[k + 'Cols'].push(i); else if (r[k] === -1) r[k] = i; break; }
        }
    });
    return r;
}
// === DIP 2.0 Grouper ===
var _dipDx=[],_dipDx2=[],_dipPx=[],_dipPx2=[];
var _dipProv={
'gd_meizhou':{name:'广东·梅州',note:'梅市医保〔2025〕4号 | 4477组 | 基准病种1000分',basePv:1100,pvNote:'2025参考 ~1100元/分(1000分基准)',lv:{'1.000':'三级甲等','0.944':'三级其他','0.889':'二级(县医院/中医院)','0.828':'二级专科','0.777':'一级中心镇','0.677':'一级乡镇'},ad:{age:[[0,6,1.053],[7,120,1.0]]},cci:{0.95:'无合并症',1.0:'一般',1.35:'重症CCI>=3'},extra:'基层500组同价；中医37种；6岁以下+5.3%',cciSys:'国标MCC/CC(二元判断)'},
'fj_xiamen':{name:'福建·厦门',note:'厦医保中心〔2024〕40号 | 5000+组',basePv:12500,pvNote:'2025参考 ~12,500元/分(年度核定)',lv:{'0.93':'三级','0.72':'二级','0.55':'一级'},ad:{age:[[0,6,1.06],[7,69,1.0],[70,200,1.03]]},cci:{0.95:'CCI=0',1.0:'CCI=1',1.15:'CCI=2',1.25:'CCI=3',1.35:'CCI>=4'},extra:'R1=L0+L1+L2+L3+L5；CMI加成(每高5%+0.01)',cciSys:'<b>厦门CCI分型</b>：多级加权叠加(CCI=合并症指数，每级独立系数，多合并症可累加，区别于DRG二元MCC/CC)'},
'js_lyg':{name:'江苏·连云港',note:'连医保〔17〕号 2025版 | 5385组 | 196重症辅助组',basePv:11500,pvNote:'2025参考 ~11,500元/分(苏北)',lv:{'1.00':'三级','0.85':'二级','0.70':'一级'},ad:{age:[[0,6,1.05],[7,120,1.0]]},cci:{0.95:'无合并症',1.0:'一般',1.2:'严重并发症',1.35:'极严重并发症'},extra:'基层107个同价；中医8个+10%；1:2:7加权',cciSys:'<b>连云港196重症辅助组</b>：在主目录基础上，对含严重/极严重并发症的特定病种组合单独调高分值(两档)，非全编码覆盖'},
'sd':{name:'山东',note:'全省统一 | 160基础病种+11中医优势',basePv:13000,pvNote:'参考 ~13,000元/分(1:2:7加权)',lv:{'1.00':'三级','0.85':'二级','0.70':'一级'},ad:{age:[[0,6,1.05],[7,120,1.0]]},cci:{0.95:'无合并症',1.0:'一般',1.35:'重症'},extra:'特例单议1-3‰；22项绩效评价',cciSys:'国标MCC/CC(二元判断)'}
};
function dipVer(){var pv=document.getElementById('dip-ver').value;var info=document.getElementById('dip-ver-info');var tabs=document.getElementById('dip-prov-tabs');var sep=document.getElementById('dip-sep');
if(!pv){info.innerHTML='国家 DIP 2.0 版 · 9,520组核心病种(手术6,311+保守3,209) · 覆盖率95%+ · 各省点值=年度基金预算/总分值(每年核定)';resetDipParams();document.getElementById('dip-prov-params').style.display='none';dipCalc();tabs.style.display='none';sep.textContent='DIP 2.0 核心病种库';sd();return}
var pr=_dipProv[pv];if(!pr)return;info.innerHTML='<b>'+pr.name+'</b> | '+pr.note+(pr.pvNote?'<br>'+pr.pvNote:'')+(pr.cciSys?'<br><span style="color:var(--accent)">'+pr.cciSys+'</span>':'');var lvSel=document.getElementById('dip-lv');lvSel.innerHTML='';for(var v in pr.lv){lvSel.innerHTML+='<option value="'+v+'">'+pr.lv[v]+' '+v+'</option>'};document.getElementById('dpv').value=pr.basePv;var agSel=document.getElementById('dip-age');agSel.innerHTML='';if(pr.ad&&pr.ad.age){pr.ad.age.forEach(function(a){agSel.innerHTML+='<option value="'+a[2]+'">'+(a[0]===0?'<'+a[1]+'岁':(a[0]===a[1]?a[0]+'岁':a[0]+'-'+a[1]+'岁'))+' x'+a[2]+'</option>'})};var ccSel=document.getElementById('dip-cci');ccSel.innerHTML='';for(var c in pr.cci){ccSel.innerHTML+='<option value="'+c+'">'+pr.cci[c]+' x'+c+'</option>'};
// Show province tabs and load data
var cat=_dipProvCatalog[pv];
if(cat&&!cat._xm&&!cat._loading&&!cat._core&&!cat._loading){_dipProvLoad(pv)}else if(cat&&(cat._core&&cat._core.length||cat._xm&&cat._xm.length)){tabs.style.display='flex';if(pv==='fj_xiamen'){_xmSubTab(_xmActiveSub||'main')}else{document.querySelectorAll('.dip-ptab').forEach(function(b,i){if(i===1)b.textContent='综合病种';if(i===3){b.style.display=cat&&cat.fixed?'':'none'}})}}else{tabs.style.display='none';sep.textContent='DIP 2.0 核心病种库'}
document.getElementById('dip-prov-params').style.display='';dipCalc();sd()}
function resetDipParams(){var lv=document.getElementById('dip-lv');lv.innerHTML='<option value="1.0">三级 1.0</option><option value="0.8">二级 0.8</option><option value="0.6">一级 0.6</option>';document.getElementById('dpv').value=13000;var ag=document.getElementById('dip-age');ag.innerHTML='<option value="1.0">18-45岁 1.0</option><option value="2.8"><1岁 2.8</option><option value="1.6">>76岁 1.6</option>';var cc=document.getElementById('dip-cci');cc.innerHTML='<option value="1.0">无合并症 1.0</option><option value="0.95">CCI=0 0.95</option><option value="1.35">CCI>=3 1.35</option>'}
function adipp(c,n){if(!c){var q=document.getElementById('dip-di').value.trim().toUpperCase();var f=D.m10[q]||f10all(q,1)[0];if(f){c=f.c;n=f.n}document.getElementById('dip-di').value=''}if(c){_dipDx=[{c:c,n:n}];rdip();document.getElementById('dip-ds').style.display='none'}}
function adipp2(c,n){if(!c){var q=document.getElementById('dip-d2').value.trim().toUpperCase();var f=D.m10[q]||f10all(q,1)[0];if(f){c=f.c;n=f.n}document.getElementById('dip-d2').value=''}if(c){_dipDx2.push({c:c,n:n});rdip();document.getElementById('dip-d2s').style.display='none'}}
function adippx(c,n){if(!c){var q=document.getElementById('dip-pi').value.trim();var f=D.m9[q]||f9all(q,1)[0];if(f){c=f.c;n=f.n}document.getElementById('dip-pi').value=''}if(c){_dipPx=[{c:c,n:n}];rdip();document.getElementById('dip-ps').style.display='none'}}
function adippx2(c,n){if(!c){var q=document.getElementById('dip-p2').value.trim();var f=D.m9[q]||f9all(q,1)[0];if(f){c=f.c;n=f.n}document.getElementById('dip-p2').value=''}if(c){_dipPx2.push({c:c,n:n});rdip();document.getElementById('dip-p2s').style.display='none'}}
function rdip(){document.getElementById('dip-dc').innerHTML=_dipDx.map(function(d){return'<span class="chip chip-p">⭐ '+d.c+' '+d.n+' <span class="chip-x" onclick="_dipDx=[];rdip();dipCalc()">x</span></span>'}).join('');document.getElementById('dip-d2c').innerHTML=_dipDx2.map(function(d,i){return'<span class="chip">'+d.c+' '+d.n+' <span class="chip-x" onclick="_dipDx2.splice('+i+',1);rdip();dipCalc()">x</span></span>'}).join('');document.getElementById('dip-pc').innerHTML=_dipPx.map(function(p){return'<span class="chip chip-p">⭐ '+p.c+' '+p.n+' <span class="chip-x" onclick="_dipPx=[];rdip();dipCalc()">x</span></span>'}).join('');document.getElementById('dip-p2c').innerHTML=_dipPx2.map(function(p,i){return'<span class="chip">'+p.c+' '+p.n+' <span class="chip-x" onclick="_dipPx2.splice('+i+',1);rdip();dipCalc()">x</span></span>'}).join('')}
function sdip(iid,bid){clearTimeout(_st);_st=setTimeout(function(){var q=document.getElementById(iid).value.trim(),box=document.getElementById(bid);if(!q||q.length<1){box.style.display='none';return}var m=f10all(q);if(!m.length){box.style.display='none';return}box.style.display='block';var fn=iid==='dip-d2'?'adipp2':'adipp';var mccS=_drg?_drg.mccS:new Set,ccS=_drg?_drg.ccS:new Set;box.innerHTML=m.map(function(c){var sn=c.n.replace(/'/g,'');var tags='';if(mccS.has(c.c))tags+='<span style="color:var(--danger);font-weight:600;font-size:.72em">MCC</span> ';else if(ccS.has(c.c))tags+='<span style="color:var(--warning);font-size:.72em">CC</span> ';return'<div class="si" onclick="document.getElementById(\''+bid+'\').style.display=\'none\';'+fn+'(\''+c.c+'\',\''+sn+'\')"><span class="sc">'+c.c+'</span><span class="sn">'+sn+'</span>'+tags+'</div>'}).join('')},200)}

function spdip(iid,bid){clearTimeout(_st);_st=setTimeout(function(){var q=document.getElementById(iid).value.trim(),box=document.getElementById(bid);if(!q||q.length<1){box.style.display='none';return}var m=f9all(q);if(!m.length){box.style.display='none';return}box.style.display='block';var fn=bid==='dip-p2s'?'adippx2':'adippx';box.innerHTML=m.map(function(c){var sn=c.n.replace(/'/g,'');return'<div class="si" onclick="document.getElementById(\''+bid+'\').style.display=\'none\';'+fn+'(\''+c.c+'\',\''+sn+'\')"><span class="sc">'+c.c+'</span><span class="sn">'+sn+'</span></div>'}).join('')},200)}
function dipCalc(){if(!_dipDx.length){document.getElementById('dip-rr').innerHTML='<div class="emp"><p>请先添加主要诊断编码</p></div>';return}if(!D||!D.dip){document.getElementById('dip-rr').innerHTML='<div class="emp"><p>数据加载中...</p></div>';return}var dx=_dipDx[0],px=_dipPx[0],pv=parseFloat(document.getElementById('dpv').value)||13000,il=parseFloat(document.getElementById('dip-lv').value),ag=parseFloat(document.getElementById('dip-age').value),ci=parseFloat(document.getElementById('dip-cci').value);var allPx=_dipPx.concat(_dipPx2);var matches=[];D.dip.forEach(function(d){if(d.dx===dx.c){var sc=0;if(allPx.length>0){for(var i=0;i<allPx.length;i++){if(d.px===allPx[i].c){sc=Math.max(sc,3);break}else if(d.rpx===allPx[i].c){sc=Math.max(sc,2)}}if(sc===0)sc=1}else{sc=d.px?0:1}if(sc>0)matches.push({d:d,score:sc})}});if(!matches.length&&allPx.length>0){var fuzzy=[];D.dip.forEach(function(d){if(d.dx&&dx.c&&(d.dx.startsWith(dx.c)||dx.c.startsWith(d.dx))){var sc=0.5;for(var i=0;i<allPx.length;i++){if(d.px===allPx[i].c||d.rpx===allPx[i].c){sc=Math.max(sc,1.5);break}}if(sc>0)fuzzy.push({d:d,score:sc})}});if(fuzzy.length){fuzzy.sort(function(a,b){return b.score-a.score});matches=fuzzy.slice(0,5)}}if(!matches.length){document.getElementById('dip-rr').innerHTML='<div class="emp"><p>未找到匹配的 DIP 病种组</p><p style="font-size:.78em;color:var(--text-dim)">诊断: '+dx.c+' '+dx.n+(allPx.length?' | 手术: '+allPx.map(function(p){return p.c}).join(', '):'')+'</p><p style="font-size:.78em;color:var(--text-dim)">该诊断/手术组合暂不在国家 DIP 2.0 核心病种库中</p></div>';return}matches.sort(function(a,b){return b.score-a.score});
// === CCI auto-detection from MCC/CC lists ===
var mccS=_drg?_drg.mccS:new Set,ccS=_drg?_drg.ccS:new Set,excl=_drg?_drg.excl:{},mccT=_drg?_drg.mccT:{},ccT=_drg?_drg.ccT:{};
var cciDx=[],cciLevel='无合并症',cciAuto=1.0;
// Check primary diagnosis
if(mccS.has(dx.c)){var tbl=mccT[dx.c]||'',exclCodes=excl[tbl]||[];if(exclCodes.indexOf(dx.c)<0){cciDx.push({c:dx.c,l:'MCC(严重)'});cciLevel='MCC(严重合并症)';cciAuto=1.35}}
else if(ccS.has(dx.c)){var tbl2=ccT[dx.c]||'',exclCodes2=excl[tbl2]||[];if(exclCodes2.indexOf(dx.c)<0){cciDx.push({c:dx.c,l:'CC(一般)'});cciLevel='CC(一般合并症)';cciAuto=1.0}}
if(cciDx.length===0&&mccS.has(dx.c)){cciDx.push({c:dx.c,l:'MCC(已排除)'});cciLevel='MCC(排除-与主诊冲突)'}
// Use auto-detected or manual CCI
var effCI=ci!==1.0?ci:cciAuto;
var html='<div class="clr"><h3 style="color:var(--success);margin-bottom:2px">匹配 '+matches.length+' 个 DIP 病种组</h3>';
html+='<div style="font-size:.78em;color:var(--text-dim);margin-bottom:12px">主诊: '+dx.c+' '+dx.n+(px?' | 主手术: '+px.c+' '+px.n:'')+(allPx.length>1?' | 其他手术: '+_dipPx2.map(function(p){return p.c}).join(', '):'')+' | 点值 '+pv.toLocaleString()+' | 系数 '+il.toFixed(2)+'×'+ag.toFixed(1)+'×'+effCI.toFixed(2)+(cciDx.length?' <span style="color:'+(cciLevel.indexOf('MCC')>=0?'var(--danger)':'var(--warning)')+'">[CCI: '+cciLevel+']</span>':'')+'</div>';
html+='<div style="display:flex;flex-direction:column;gap:8px">';matches.slice(0,5).forEach(function(m,i){var d=m.d,isTop=i===0;var estScore=Math.round(2000+parseInt(d.c.replace('DIP',''))*8);var pay=Math.round(estScore*pv/13000*il*ag*effCI);html+='<div class="dip-result-card'+(isTop?' primary':'')+'">';html+='<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap"><b style="font-size:1.05em;color:'+(isTop?'var(--accent)':'var(--text)')+'">'+d.c+'</b>';if(isTop)html+='<span style="font-size:.7em;padding:1px 6px;border-radius:6px;background:var(--accent);color:#fff">推荐</span>';html+='<span style="font-size:.78em;color:var(--text-dim)">'+(d.px?d.px+' '+d.pxn:'保守治疗')+'</span></div>';html+='<div style="font-size:.75em;color:var(--text-dim);margin-top:4px">诊断: '+d.dx+' '+d.dxn+'</div>';if(d.rpx)html+='<div style="font-size:.72em;color:var(--text-dim)">相关手术: '+d.rpx+' '+d.rpxn+'</div>';html+='<div style="font-size:.75em;margin-top:6px;padding-top:6px;border-top:1px dotted var(--border);display:flex;gap:14px;flex-wrap:wrap;align-items:center"><span>估算分值 <b style="color:'+(isTop?'var(--accent)':'var(--text-dim)')+'">'+estScore+'</b></span>'+(isTop?'<span>点值 <b>'+pv.toLocaleString()+'</b></span><span>等级系数 <b>'+il.toFixed(1)+'</b></span><span>年龄 <b>'+ag.toFixed(1)+'</b></span><span>CCI <b style="color:'+(effCI>1.0?'var(--danger)':'var(--text-dim)')+'">'+effCI.toFixed(2)+'</b></span>':'')+'<span style="font-size:.9em">≈ 预估支付 <b style="color:'+(isTop?'var(--success)':'var(--text)')+'">'+pay.toLocaleString()+'</b> 元</span></div>'});html+='</div><div style="font-size:.68em;color:var(--text-dim);margin-top:10px;padding-top:8px;border-top:1px dotted var(--border)">* 分值按DIP编码序号估算(实际由各地测定)；点值=年度基金预算÷总分值(每年核定)；CCI基于CHS-DRG 2.0国标MCC/CC自动检测(4477+8008条编码)'+(cciDx.length?' | 本次检测: '+cciDx.map(function(x){return x.c+'['+x.l+']'}).join(', '):'')+'</div></div>';document.getElementById('dip-rr').innerHTML=html}


// Province-specific DIP data (loaded separately when available)
var _dipProvCatalog={
	'gd_meizhou':{name:'广东·梅州',prefix:'gd',total:4477,core:3646,composite:793,tcm:37,grassroots:500,baseScore:1000,source:'梅市医保〔2025〕4号',sourceUrl:'http://www.gdmx.gov.cn/zwgk/tzgg/content/post_2754625.html',groups:null},
	'fj_xiamen':{name:'福建·厦门',prefix:'xm',total:5226,core:4539,composite:687,source:'厦医保中心〔2025〕',sourceUrl:'https://ylbz.xm.gov.cn/zwgk/zfxxgk/ml/zcwj/ybzx/202509/t20250930_2958855.htm',groups:null},
	'js_lyg':{name:'江苏·连云港',prefix:'lyg',total:5588,core:4433,composite:1158,tcm:9,fixed:87,source:'连医保〔2025〕17号',sourceUrl:'https://www.lyg.gov.cn/zglygzfmhwz/zcwj_ylws/content/f128e533-4e0f-4ef2-8717-9f96975f1842.html',groups:null}
};
var _dipActiveTab='core';var _xmActiveSub='main';
function _dipProvTab(tab){
	_dipActiveTab=tab;
	var isXm=document.getElementById("dip-ver").value=="fj_xiamen";
	if(isXm){_xmSubTab(tab);return}
		var cat=_dipProvCatalog[document.getElementById("dip-ver").value];
			var btns=document.querySelectorAll(".dip-ptab");
		btns.forEach(function(b,i){
		b.style.display="";
		if(i===1)b.textContent="综合病种";
		if(i===3){b.textContent="定额病种";b.style.display=cat&&cat.fixed?"":"none";}
		b.classList.toggle("active",(tab=="core"&&i===0)||(tab=="comp"&&i===1)||(tab=="tcm"&&i===2)||(tab=="fixed"&&i===3));
		});
	sd();
}
function _xmSubTab(sub){
	_xmActiveSub=sub||'main';
	if(sub==='core')_xmActiveSub='main';
	if(sub==='comp')_xmActiveSub='main';
	if(sub==='tcm')_xmActiveSub='main';
	var tabs=document.getElementById('dip-prov-tabs');
	tabs.style.display='flex';
	var labels=[['main','核心和综合病种'],['bed','床日病种'],['day','日间病种'],['eqg','等价病种组'],['eq','等价组合'],['inv','无效编码'],['opd','门诊病种']];
	tabs.innerHTML=labels.map(function(l){return '<button class="dip-ptab'+(l[0]===_xmActiveSub?' active':'')+'" onclick="_xmSubTab(\''+l[0]+'\')">'+l[1]+'</button>'}).join('');
	sd();
}
function _dipProvLoad(ver){
var cat=_dipProvCatalog[ver];
if(!cat||cat._loading)return;
cat._loading=true;
var tabs=document.getElementById('dip-prov-tabs');
var info=document.getElementById('id');
info.textContent='正在加载 '+cat.name+' 分值库...';
var isXm=ver==='fj_xiamen';
var need=isXm?2:(cat.fixed?4:3),got=0,errs=[];
function tryDone(){
got++;
if(got>=need){
cat._loading=false;
	if(isXm){cat._xm=cat._all||[];cat._core=null;cat._comp=null;cat._tcm=null;}
	else{cat._core=cat._core||[];cat._comp=cat._comp||[];cat._tcm=cat._tcm||[];cat._fixed=cat._fixed||[];}
var s=document.getElementById('dip-sep');
s.innerHTML='';
var isXmT=ver==='fj_xiamen';
if(isXmT){tabs.style.display='flex';_xmSubTab('main');}
else{tabs.style.display='flex';_dipActiveTab='core';
document.querySelectorAll('.dip-ptab').forEach(function(b,i){b.classList.toggle('active',i===0);if(i===1)b.textContent='综合病种'});}
sd();
}
}
if(isXm){
fetch('dip_fj_xiamen.json').then(function(r){if(!r.ok)throw new Error('HTTP'+r.status);return r.json()}).then(function(d){cat._all=d;info.textContent=cat.name+' 核心和综合病种: '+d.length+'条';tryDone()}).catch(function(e){errs.push(e.message);tryDone()});
fetch('dip_fj_xm_subs.json').then(function(r){if(!r.ok)throw new Error('subs HTTP'+r.status);return r.json()}).then(function(d){cat._subs=d;tryDone()}).catch(function(e){errs.push('subs:'+e.message);tryDone()});
	}else{
	var pfx=cat.prefix||'gd';
	var types=['core','comp','tcm'];
	if(cat.fixed)types.push('fixed');
	var idx=0;
		function loadNext(){
		if(idx>=types.length)return;
		var t=types[idx++];
		fetch('dip_'+pfx+'_'+t+'.json').then(function(r){if(!r.ok)throw new Error(t+' HTTP'+r.status);return r.json()}).then(function(d){cat['_'+t]=d;info.textContent=cat.name+' '+t+' 加载完成: '+d.length+'条';tryDone();loadNext()}).catch(function(e){errs.push(t+':'+e.message);tryDone();loadNext()});
		}
		loadNext();}
}

function _xmBedExpand(rid){
	var nr=document.getElementById('h_'+rid);
	if(!nr)return;
	if(nr.style.display==='none'){
	nr.style.display='';
	var ver=document.getElementById('dip-ver').value;
	var cat=_dipProvCatalog[ver];
	var bed=cat&&cat._subs?cat._subs.bed:null;
	var d=null;
	if(bed){for(var i=0;i<bed.length;i++){if(('bed'+bed[i].code.replace(/[^a-zA-Z0-9]/g,'_'))===rid){d=bed[i];break}}}
	var hc=document.getElementById('hc_'+rid);
	if(d){
	var h='<div style="padding:8px 14px;font-size:.78em;line-height:1.8;display:grid;grid-template-columns:auto 1fr;gap:3px 16px">';
	if(d.dtype)h+='<span style="color:var(--text-dim)">辅助目录类型:</span><span>'+d.dtype+'</span>';
	if(d.stages&&d.stages.length){
	h+='<span style="color:var(--text-dim)">疾病分期:</span><span>';
	for(var i=0;i<d.stages.length;i++){
	h+=d.stages[i].stage+' (调整系数 x'+d.stages[i].adj+')';
	if(i<d.stages.length-1)h+='<br>';
	}
	h+='</span>';
	}
	if(d.note)h+='<span style="color:var(--text-dim)">备注:</span><span>'+d.note+'</span>';
	h+='</div>';
	hc.innerHTML=h;
	}
	}else nr.style.display='none';
}
function _xmExpand(rid,code){
	var nr=document.getElementById('h_'+rid);
	if(!nr)return;
	if(nr.style.display==='none'){
	nr.style.display='';
	var ver=document.getElementById('dip-ver').value;
	var cat=_dipProvCatalog[ver];
	var all=cat?cat._xm||cat._all:null;
	var d=null;
	if(all){for(var i=0;i<all.length;i++){if(all[i].c===code||all[i].l3===code){d=all[i];break}}}if(!d&&cat&&cat._subs&&cat._subs.day){for(var i=0;i<cat._subs.day.length;i++){if(cat._subs.day[i].c===code||cat._subs.day[i].l3===code){d=cat._subs.day[i];break}}}
	var hc=document.getElementById('hc_'+rid);
	if(d){
	var h='<div style="padding:8px 14px;font-size:.78em;line-height:1.8;display:grid;grid-template-columns:auto 1fr;gap:3px 16px">';
	h+='<span style="color:var(--text-dim)">一级目录:</span><span>'+(d.l1||'—')+' '+(d.l1n||'')+'</span>';
	h+='<span style="color:var(--text-dim)">二级目录:</span><span>'+(d.l2||'—')+' '+(d.l2n||'')+'</span>';
	h+='<span style="color:var(--text-dim)">三级目录:</span><span>'+(d.c||d.l3||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">目录类型:</span><span>'+(d.dtype||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">期初权重:</span><span>'+(d.weight||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">备注:</span><span>'+(d.note||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">辅助目录:</span><span>'+(d.aux||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">调整系数:</span><span>'+(d.aux_coef||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">辅助目录说明:</span><span>'+(d.aux_desc||'—')+'</span>';
	h+='</div>';
	hc.innerHTML=h;
	}
	}else nr.style.display='none';
}
function _lygCoreExpand(rid,code){
	var nr=document.getElementById('h_'+rid);
	if(!nr)return;
	if(nr.style.display==='none'){
	nr.style.display='';
	var ver=document.getElementById('dip-ver').value;
	var cat=_dipProvCatalog[ver];
	var core=cat?cat._core:null;
	var d=null;
	if(core){for(var i=0;i<core.length;i++){if(core[i].c===code){d=core[i];break}}}
	var hc=document.getElementById('hc_'+rid);
	if(d){
	var h='<div style="padding:8px 14px;font-size:.78em;line-height:1.8;display:grid;grid-template-columns:auto 1fr;gap:3px 16px">';
	h+='<span style="color:var(--text-dim)">三级医院等级系数:</span><span>'+(d.coef3||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">二级医院等级系数:</span><span>'+(d.coef2||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">一级医院等级系数:</span><span>'+(d.coef1||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">病种类型:</span><span>'+(d.dtype||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">备注:</span><span>'+(d.note||'—')+'</span>';
	h+='</div>';
	hc.innerHTML=h;
	}
	}else nr.style.display='none';
}

// === LYG Comp Expand ===
function _lygCompExpand(rid,code){
	var nr=document.getElementById('h_'+rid);
	if(!nr)return;
	if(nr.style.display==='none'){
	nr.style.display='';
	var ver=document.getElementById('dip-ver').value;
	var cat=_dipProvCatalog[ver];
	var comp=cat?cat._comp:null;
	var d=null;
	if(comp){for(var i=0;i<comp.length;i++){if(comp[i].c===code){d=comp[i];break}}}
	var hc=document.getElementById('hc_'+rid);
	if(d){
	var h='<div style="padding:8px 14px;font-size:.78em;line-height:1.8;display:grid;grid-template-columns:auto 1fr;gap:3px 16px">';
	h+='<span style="color:var(--text-dim)">三级医院等级系数:</span><span>'+(d.coef3||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">二级医院等级系数:</span><span>'+(d.coef2||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">一级医院等级系数:</span><span>'+(d.coef1||'—')+'</span>';
	h+='</div>';
	hc.innerHTML=h;
	}
	}else nr.style.display='none';
}
// === LYG TCM Expand ===
function _lygTcmExpand(rid,code){
	var nr=document.getElementById('h_'+rid);
	if(!nr)return;
	if(nr.style.display==='none'){
	nr.style.display='';
	var ver=document.getElementById('dip-ver').value;
	var cat=_dipProvCatalog[ver];
	var tcm=cat?cat._tcm:null;
	var d=null;
	if(tcm){for(var i=0;i<tcm.length;i++){if(tcm[i].c===code){d=tcm[i];break}}}
	var hc=document.getElementById('hc_'+rid);
	if(d){
	var h='<div style="padding:8px 14px;font-size:.78em;line-height:1.8;display:grid;grid-template-columns:auto 1fr;gap:3px 16px">';
	h+='<span style="color:var(--text-dim)">三级医院等级系数:</span><span>'+(d.coef3||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">二级医院等级系数:</span><span>'+(d.coef2||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">一级医院等级系数:</span><span>'+(d.coef1||'—')+'</span>';
	h+='<span style="color:var(--text-dim)">评价指标:</span><span>'+(d.eval||'—')+'</span>';
	h+='</div>';
	hc.innerHTML=h;
	}
	}else nr.style.display='none';
}

function _dipGetSrc(){
var ver=document.getElementById('dip-ver').value;
var cat=_dipProvCatalog[ver];
if(cat&&cat._xm&&cat._xm.length){
if(_xmActiveSub==='bed')return cat._subs?cat._subs.bed:null;
if(_xmActiveSub==='day')return cat._subs?cat._subs.day:null;
if(_xmActiveSub==='eqg')return cat._subs?cat._subs.eqg:null;
if(_xmActiveSub==='eq')return cat._subs?cat._subs.eq:null;
if(_xmActiveSub==='inv')return cat._subs?cat._subs.inv:null;
if(_xmActiveSub==='opd')return cat._subs?cat._subs.opd:null;
return cat._xm;
}
var tab=_dipActiveTab||'core';
if(tab==='fixed'&&cat&&cat._fixed&&cat._fixed.length)return cat._fixed;
if(cat&&cat['_'+tab]&&cat['_'+tab].length)return cat['_'+tab];
if(cat&&cat._core&&cat._core.length)return cat._core;
if(D&&D.dip)return D.dip;
return null;
}
function _dipRenderRow(d,isProv){
	var h='<tr>';
	var ver=document.getElementById('dip-ver').value;
	if(!((ver==='fj_xiamen'&&['bed','eqg','eq','inv','opd'].indexOf(_xmActiveSub)>=0)||_dipActiveTab==='fixed')){
	h+='<td><span class="tag ta">'+(d.c||d.l3||'')+'</span></td>';
	}
	if(!isProv){
	h+='<td><span class="tag">'+(d.dx||'')+'</span> '+(d.dxn||'')+'</td>';
	h+='<td>'+(d.px?'<span class="tag tp">'+d.px+'</span> '+(d.pxn||''):'—')+'</td>';
	h+='<td>'+(d.rpx?'<span class="tag ts">'+d.rpx+'</span> '+(d.rpxn||''):'—')+'</td>';
	}else if(ver==='fj_xiamen'&&_xmActiveSub==='main'){
	var rid='xm'+d.c.replace(/[^a-zA-Z0-9]/g,'_');
	h+='<td style="font-size:.75em">'+(d.l3n||'')+'</td>';
	h+='<td><span class="tag">'+(d.dx||'')+'</span></td>';
	h+='<td style="font-size:.78em">'+(d.dxn||'—')+'</td>';
	h+='<td>'+(d.px?'<span class="tag tp">'+d.px+'</span>':'—')+'</td>';
	h+='<td style="font-size:.78em">'+(d.pxn||'—')+'</td>';
	h+='<td>'+(d.rpx?'<span class="tag ts">'+d.rpx+'</span>':'—')+'</td>';
	h+='<td style="font-size:.78em">'+(d.rpxn||'—')+'</td>';
	h+='<td style="text-align:right;font-weight:600;color:var(--accent)">'+(d.score||'—')+'</td>';
	h+='<td style="text-align:right;font-size:.82em">'+(d.weight||'—')+'</td>';
	h+='<td style="text-align:right;cursor:pointer;color:var(--accent);font-weight:600" onclick="event.stopPropagation();_xmExpand(\''+rid+'\',\''+(d.c||'').replace(/'/g,'')+'\')">'+(d.aux_coef||'—')+' ▸</td>';
	h+='</tr>';
	h+='<tr id="h_'+rid+'" style="display:none;background:var(--bg-input)"><td colspan="11" id="hc_'+rid+'"></td></tr>';
	}else if(ver==='fj_xiamen'&&_xmActiveSub==='bed'){
	var rid='bed'+(d.code||'').replace(/[^a-zA-Z0-9]/g,'_');
	h+='<td style="font-weight:500">'+(d.name||'—')+'</td>';
	h+='<td><span class="tag">'+(d.code||'')+'</span></td>';
	h+='<td style="text-align:right;font-weight:600;color:var(--accent)">'+(d.pay3||'—')+'</td>';
	h+='<td style="text-align:right">'+(d.pay2||'—')+'</td>';
	h+='<td style="text-align:right;cursor:pointer;color:var(--accent);font-weight:600" onclick="event.stopPropagation();_xmBedExpand(\''+rid+'\')">'+(d.pay1||'—')+' ▸</td>';
	h+='</tr>';
	h+='<tr id="h_'+rid+'" style="display:none;background:var(--bg-input)"><td colspan="5" id="hc_'+rid+'"></td></tr>';
	}else if(ver==='fj_xiamen'&&_xmActiveSub==='day'){
	var rid='xm'+(d.l3||'').replace(/[^a-zA-Z0-9]/g,'_');
	h+='<td style="font-size:.75em">'+(d.l3n||'')+'</td>';
	h+='<td><span class="tag">'+(d.dx||'')+'</span></td>';
	h+='<td style="font-size:.78em">'+(d.dxn||'—')+'</td>';
	h+='<td>'+(d.px?'<span class="tag tp">'+d.px+'</span>':'—')+'</td>';
	h+='<td style="font-size:.78em">'+(d.pxn||'—')+'</td>';
	h+='<td>'+(d.rpx?'<span class="tag ts">'+d.rpx+'</span>':'—')+'</td>';
	h+='<td style="font-size:.78em">'+(d.rpxn||'—')+'</td>';
	h+='<td style="text-align:right;font-weight:600;color:var(--accent)">'+(d.score||'—')+'</td>';
	h+='<td style="text-align:right;font-size:.82em">'+(d.weight||'—')+'</td>';
	h+='<td style="text-align:right;cursor:pointer;color:var(--accent);font-weight:600" onclick="event.stopPropagation();_xmExpand(\''+rid+'\',\''+((d.c||d.l3)||'').replace(/'/g,'')+'\')">'+(d.aux_coef||'—')+' ▸</td>';
	h+='</tr>';
	h+='<tr id="h_'+rid+'" style="display:none;background:var(--bg-input)"><td colspan="11" id="hc_'+rid+'"></td></tr>';
	}else if(ver==='fj_xiamen'&&_xmActiveSub==='eqg'){
	h+='<td><span class="tag ta">'+(d.code||'')+'</span></td>';
	h+='<td style="font-weight:500">'+(d.name||'—')+'</td>';
	h+='<td style="font-size:.75em">'+(d.scope||'—')+'</td>';
	h+='<td style="font-size:.75em">'+(d.desc||'—')+'</td>';
	h+='<td style="font-size:.72em">'+(d.note||'—')+'</td>';
	}else if(ver==='fj_xiamen'&&_xmActiveSub==='eq'){
	h+='<td><span class="tag ta">'+(d.gcode||'')+'</span></td>';
	h+='<td style="font-size:.82em">'+(d.gname||'—')+'</td>';
	h+='<td style="text-align:center">'+(d.seq||'—')+'</td>';
	h+='<td><span class="tag ts">'+(d.opcode||'')+'</span></td>';
	h+='<td style="font-size:.78em">'+(d.opname||'—')+'</td>';
	h+='<td><span class="tag">'+(d.eqcombo||'—')+'</span></td>';
	h+='<td style="font-size:.78em">'+(d.cat||'—')+'</td>';
	h+='<td style="font-size:.78em">'+(d.catname||'—')+'</td>';
	}else if(ver==='fj_xiamen'&&_xmActiveSub==='inv'){
		if(d.gray){
		h=h.replace('<tr>','<tr style="background:#e8e8e8;color:#888">');
		h+='<td style="background:#e8e8e8;color:#888"><span class="tag" style="background:#d0d0d0;color:#777;border:1px solid #ccc">'+(d.code||'')+'</span></td>';
		h+='<td style="font-size:.82em;background:#e8e8e8;color:#888">'+(d.name||'—')+'</td>';
		h+='<td style="background:#e8e8e8"><span class="tag" style="background:var(--danger-light);color:var(--danger)">'+(d.tag||'—')+'</span></td>';
		h+='<td style="font-size:.72em;background:#e8e8e8;color:#888">'+(d.note||'—')+'</td>';
		}else{
		h+='<td><span class="tag ts">'+(d.code||'')+'</span></td>';
		h+='<td style="font-size:.82em">'+(d.name||'—')+'</td>';
		h+='<td><span class="tag" style="background:var(--danger-light);color:var(--danger)">'+(d.tag||'—')+'</span></td>';
		h+='<td style="font-size:.72em">'+(d.note||'—')+'</td>';
		}
	}else if(ver==='fj_xiamen'&&_xmActiveSub==='opd'){
	h+='<td style="font-weight:500">'+(d.name||'—')+'</td>';
	h+='<td><span class="tag">'+(d.dx||'')+'</span></td>';
	h+='<td style="font-size:.78em">'+(d.dxn||'—')+'</td>';
	h+='<td>'+(d.px!=='-'?'<span class="tag ts">'+d.px+'</span>':'—')+'</td>';
	h+='<td style="font-size:.78em">'+(d.pxn!=='-'?d.pxn:'—')+'</td>';
	h+='<td style="text-align:right;font-weight:600;color:var(--accent)">'+(d.score||'—')+'</td>';
	h+='<td style="font-size:.72em">'+(d.note||'—')+'</td>';
			}else if(_dipActiveTab==='tcm' && ver==='js_lyg'){
		var rid='lygt'+d.c.replace(/[^a-zA-Z0-9]/g,'_');
		h+='<td style="font-weight:500">'+(d.tcmn||'—')+'</td>';
		h+='<td><span class="tag">'+(d.tcd||'—')+'</span></td>';
		h+='<td style="font-size:.82em">'+(d.dxn||'—')+'</td>';
		h+='<td><span class="tag">'+(d.dx||'')+'</span></td>';
		h+='<td>'+(d.pxn?'<span class="tag ts">'+d.pxn+'</span>':'—')+'</td>';
		h+='<td>'+(d.px?'<span class="tag ts">'+d.px+'</span>':'—')+'</td>';
		h+='<td style="text-align:right;font-weight:600;color:var(--accent);cursor:pointer" onclick="event.stopPropagation();_lygTcmExpand(\''+rid+'\',\''+(d.c||'').replace(/'/g,'')+'\')">'+(d.score||'—')+' ▸</td>';
		h+='</tr>';
		h+='<tr id="h_'+rid+'" style="display:none;background:var(--bg-input)"><td colspan="8" id="hc_'+rid+'"></td></tr>';
		}else if(_dipActiveTab==='tcm'){
	h+='<td><span class="tag">'+(d.icd||'')+'</span> '+(d.icdn||'')+'</td>';
	h+='<td style="font-size:.85em">'+(d.tcmn||'—')+'</td>';
	h+='<td style="font-size:.78em;color:var(--text-dim)">—</td>';
	h+='<td style="text-align:right;font-weight:600;color:var(--accent)">'+(d.score||'—')+'</td>';
			}else if(_dipActiveTab==='comp' && ver==='js_lyg'){
		var rid='lygc'+d.c.replace(/[^a-zA-Z0-9]/g,'_');
		h+='<td><span class="tag">'+(d.dx||'')+'</span></td>';
		h+='<td style="font-size:.82em">'+(d.dxn||'—')+'</td>';
		h+='<td style="font-size:.82em">'+(d.pxn||'保守治疗')+'</td>';
		h+='<td style="text-align:right;font-weight:600;color:var(--accent);cursor:pointer" onclick="event.stopPropagation();_lygCompExpand(\''+rid+'\',\''+(d.c||'').replace(/'/g,'')+'\')">'+(d.score||'—')+' ▸</td>';
		h+='</tr>';
		h+='<tr id="h_'+rid+'" style="display:none;background:var(--bg-input)"><td colspan="5" id="hc_'+rid+'"></td></tr>';
		}else if(_dipActiveTab==='comp'){
	h+='<td colspan="3" style="font-size:.82em">'+(d.name||'—')+'</td>';
		}else if(_dipActiveTab==='fixed'){
		h+='<td><span class="tag ta">'+(d.code||'')+'</span></td>';
		h+='<td style="font-weight:500">'+(d.name||'—')+'</td>';
		h+='<td><span class="tag">'+(d.type||'—')+'</span></td>';
		h+='<td style="text-align:right;font-size:.82em">'+(d.s3_score||'—')+' / '+(d.s3_fee||'—')+'</td>';
		h+='<td style="text-align:right;font-size:.82em">'+(d.s2_score||'—')+' / '+(d.s2_fee||'—')+'</td>';
		h+='<td style="text-align:right;font-size:.82em">'+(d.s1_score||'—')+' / '+(d.s1_fee||'—')+'</td>';
		h+='<td style="font-size:.78em">'+(d.insurance||'—')+'</td>';
		}else if(_dipActiveTab==='core' && ver==='js_lyg'){
		var rid='lygc'+d.c.replace(/[^a-zA-Z0-9]/g,'_');
		var isGrass=(d.note||'').indexOf('基层')>=0;
		if(isGrass)h=h.replace('<tr>','<tr style="background:var(--success-light)">');
		h+='<td><span class="tag">'+(d.dx||'')+'</span></td>';
		h+='<td style="font-size:.82em">'+(d.dxn||'—')+'</td>';
		h+='<td>'+(d.px&&d.px.length?'<span class="tag tp">'+d.px[0].c+'</span>':'—')+'</td>';
		h+='<td style="font-size:.78em">'+(d.px&&d.px.length?d.px[0].n:'—')+'</td>';
		h+='<td>'+(d.rpx&&d.rpx.length?'<span class="tag ts">'+d.rpx[0].c+'</span>':'—')+'</td>';
		h+='<td style="font-size:.78em">'+(d.rpx&&d.rpx.length?d.rpx[0].n:'—')+'</td>';
		h+='<td style="text-align:right;font-weight:600;color:var(--accent);cursor:pointer" onclick="event.stopPropagation();_lygCoreExpand(\''+rid+'\',\''+(d.c||'').replace(/'/g,'')+'\')">'+(d.score||'—')+' ▸</td>';
		h+='</tr>';
		h+='<tr id="h_'+rid+'" style="display:none;background:var(--bg-input)"><td colspan="8" id="hc_'+rid+'"></td></tr>';
	}else{
	var isGrass=(d.note||'').indexOf('基层')>=0;
	if(isGrass)h=h.replace('<tr>','<tr style="background:var(--success-light)">');
	h+='<td><span class="tag">'+(d.dx||'')+'</span> '+(d.dxn||'')+'</td>';
	var pxHtml='';
	if(d.px&&d.px.length){
	pxHtml=d.px.map(function(p){return '<div style="white-space:nowrap"><span class="tag tp">'+p.c+'</span> '+p.n+'</div>'}).join('');
	}else{pxHtml='<span style="color:var(--text-dim)">保守治疗</span>';}
	h+='<td style="font-size:.8em">'+pxHtml+'</td>';
	var rpxHtml='';
	if(d.rpx&&d.rpx.length){
	rpxHtml=d.rpx.map(function(p){return '<div style="white-space:nowrap;font-size:.85em"><span class="tag ts">'+p.c+'</span> '+p.n+'</div>'}).join('');
	}else{rpxHtml='—';}
	h+='<td style="font-size:.78em">'+rpxHtml+'</td>';
	h+='<td style="font-size:.75em">'+(d.dtype||'—')+'</td>';
	h+='<td style="text-align:right;font-weight:600;color:var(--accent)">'+(d.score||'—')+'</td>';
	}
	h+='</tr>';
	return h;
}
function sd(){
var ver=document.getElementById('dip-ver').value;
var cat=_dipProvCatalog[ver];
var isXm=ver==='fj_xiamen';var isProv=!!(cat&&(cat._core&&cat._core.length||cat._xm&&cat._xm.length));
// Province data takes priority over D.dip check
if(!isProv&&(!D||!D.dip))return;
if(cat&&!cat._core&&!cat._xm&&!cat._loading&&!cat._subs){_dipProvLoad(ver);return}
if(cat&&cat._loading){document.getElementById('bd').innerHTML='<tr><td colspan="5" class="emp">正在加载 '+cat.name+' 分值库...</td></tr>';return}
var src=_dipGetSrc();if(!src){document.getElementById('bd').innerHTML='<tr><td colspan="5" class="emp">数据加载中，请稍候...</td></tr>';return}
var q=(document.getElementById('qd').value||'').toLowerCase(),isSearch=!!q,r=src;
if(isSearch)r=r.filter(function(d){
var sq=q;
if((d.c||'').toLowerCase().includes(sq))return true;
if((d.dx||'').toLowerCase().includes(sq))return true;
if((d.dxn||d.name||'').toLowerCase().includes(sq))return true;
if(d.px&&Array.isArray(d.px)){for(var i=0;i<d.px.length;i++){if(d.px[i].c.toLowerCase().includes(sq)||d.px[i].n.toLowerCase().includes(sq))return true}}
else{if((d.px||'').toLowerCase().includes(sq)||(d.pxn||'').toLowerCase().includes(sq))return true}
if(d.rpx&&Array.isArray(d.rpx)){for(var i=0;i<d.rpx.length;i++){if(d.rpx[i].c.toLowerCase().includes(sq)||d.rpx[i].n.toLowerCase().includes(sq))return true}}
else{if((d.rpx||'').toLowerCase().includes(sq)||(d.rpxn||'').toLowerCase().includes(sq))return true}
if((d.tcmn||'').toLowerCase().includes(sq))return true;
if((d.icd||'').toLowerCase().includes(sq))return true;
		if((d.code||'').toLowerCase().includes(sq))return true;
		if((d.gcode||'').toLowerCase().includes(sq))return true;
		if((d.gname||'').toLowerCase().includes(sq))return true;
		if((d.opcode||'').toLowerCase().includes(sq))return true;
		if((d.opname||'').toLowerCase().includes(sq))return true;
		if((d.eqcombo||'').toLowerCase().includes(sq))return true;
		if((d.catname||'').toLowerCase().includes(sq))return true;
		if((d.scope||'').toLowerCase().includes(sq))return true;
		if((d.desc||'').toLowerCase().includes(sq))return true;
		if((d.tag||'').toLowerCase().includes(sq))return true;
		if((d.note||'').toLowerCase().includes(sq))return true;
			if((d.l3n||'').toLowerCase().includes(sq))return true;
			if((d.cat||'').toLowerCase().includes(sq))return true;
return false;
});
var total=r.length,show=r.slice(0,isSearch?200:100);
var info=document.getElementById('id');
var allCnt=src.length;
	var xmLabels={main:'核心和综合病种',bed:'床日病种',day:'日间病种',eqg:'DIP等价病种组',eq:'DIP等价组合',inv:'DIP无效编码',opd:'门诊DIP病种'};
	var tabLabel='';
	if(isXm){tabLabel=xmLabels[_xmActiveSub]||'核心和综合病种'}
	else if(isProv){tabLabel=_dipActiveTab=='core'?'核心病种':(_dipActiveTab=='comp'?'综合病种':'中医优势病种')}
var prName=cat?cat.name:'国家 DIP 2.0';
if(isProv&&!_dipProvLoad){} // already loaded
	var isXmH=isXm;
info.textContent=prName+' '+tabLabel+' | 共 '+allCnt.toLocaleString()+' 组'+(isSearch?' | 搜索 '+q+' 匹配 '+total+' 条':'');
// Dynamic header per tab type
var th=document.getElementById('dip-th');
		if(th){
		if(!isProv){
			th.innerHTML='<tr><th style="width:2%">DIP编码</th><th style="width:34%">主要诊断</th><th style="width:37%">主手术操作</th><th style="width:27%">相关手术</th></tr>';
		}else if(isXm&&_xmActiveSub==='main'){
			th.innerHTML='<tr><th style="width:4%">DIP编码</th><th style="width:11%">三级目录名称</th><th style="width:6%">主要诊断编码</th><th style="width:11%">主要诊断名称</th><th style="width:5%">主手术编码</th><th style="width:10%">主手术名称</th><th style="width:5%">其他手术编码</th><th style="width:10%">其他手术名称</th><th style="width:6%">标准分值</th><th style="width:5%">期初权重</th><th style="width:6%">调整系数 ▸</th></tr>';
		}else if(isXm&&_xmActiveSub==='bed'){
		th.innerHTML='<tr><th style="width:20%">病种名称</th><th style="width:18%">病种编码</th><th style="width:18%">每床日分值(三级)</th><th style="width:18%">每床日分值(二级)</th><th style="width:18%">每床日分值(一级) ▸</th></tr>';
		}else if(isXm&&_xmActiveSub==='day'){
			th.innerHTML='<tr><th style="width:4%">DIP编码</th><th style="width:11%">三级目录名称</th><th style="width:6%">主要诊断编码</th><th style="width:11%">主要诊断名称</th><th style="width:5%">主手术编码</th><th style="width:10%">主手术名称</th><th style="width:5%">其他手术编码</th><th style="width:10%">其他手术名称</th><th style="width:6%">标准分值</th><th style="width:5%">期初权重</th><th style="width:6%">调整系数 ▸</th></tr>';
		}else if(isXm&&_xmActiveSub==='eqg'){
		th.innerHTML='<tr><th style="width:10%">等价病种组编码</th><th style="width:18%">等价病种组名称</th><th style="width:38%">适用范围</th><th style="width:18%">说明</th><th style="width:10%">备注</th></tr>';
		}else if(isXm&&_xmActiveSub==='eq'){
		th.innerHTML='<tr><th style="width:9%">组编码</th><th style="width:13%">组名称</th><th style="width:7%">组内序号</th><th style="width:9%">操作编码</th><th style="width:17%">操作名称</th><th style="width:10%">等价组合</th><th style="width:10%">组合类别</th><th style="width:14%">等效类别</th></tr>';
		}else if(isXm&&_xmActiveSub==='inv'){
		th.innerHTML='<tr><th style="width:12%">编码(医保2.0)</th><th style="width:48%">名称(医保2.0)</th><th style="width:12%">标识</th><th style="width:28%">备注</th></tr>';
		}else if(isXm&&_xmActiveSub==='opd'){
		th.innerHTML='<tr><th style="width:16%">疾病名称</th><th style="width:9%">诊断编码</th><th style="width:18%">诊断名称</th><th style="width:9%">操作编码</th><th style="width:18%">操作名称</th><th style="width:9%">标准分值</th><th style="width:18%">备注</th></tr>';
		}else if(_dipActiveTab==='tcm' && ver==='js_lyg'){
			th.innerHTML='<tr><th style="width:4%">DIP编码</th><th style="width:11%">中医优势病种名称</th><th style="width:9%">中医TCD编码</th><th style="width:14%">诊断名称</th><th style="width:8%">诊断编码</th><th style="width:10%">手操名称</th><th style="width:8%">手操编码</th><th style="width:10%">病种分值 ▸</th></tr>';
			}else if(_dipActiveTab==='tcm'){
		th.innerHTML='<tr><th style="width:2%">DIP编码</th><th style="width:31%">诊断(ICD-10)</th><th style="width:27%">中医名称</th><th style="width:18%">—</th><th style="width:13%">分值</th></tr>';
		}else if(_dipActiveTab==='comp' && ver==='js_lyg'){
			th.innerHTML='<tr><th style="width:5%">DIP编码</th><th style="width:8%">主要诊断编码</th><th style="width:25%">主要诊断名称</th><th style="width:20%">主要操作名称</th><th style="width:10%">分值 ▸</th></tr>';
			}else if(_dipActiveTab==='comp'){
		th.innerHTML='<tr><th style="width:2%">DIP编码</th><th style="width:76%" colspan="3">综合病种名称</th><th style="width:14%">分值</th></tr>';
			}else if(_dipActiveTab==='fixed'){
			th.innerHTML='<tr><th style="width:10%">病种代码</th><th style="width:22%">病种名称</th><th style="width:10%">病种类型</th><th style="width:16%">三级(分值/结算)</th><th style="width:16%">二级(分值/结算)</th><th style="width:16%">一级(分值/结算)</th><th style="width:10%">参保类型</th></tr>';
		}else if(_dipActiveTab==='core' && ver==='js_lyg'){
			th.innerHTML='<tr><th style="width:5%">DIP编码</th><th style="width:8%">主要诊断编码</th><th style="width:14%">主要诊断名称</th><th style="width:9%">主要操作编码</th><th style="width:12%">主要操作名称</th><th style="width:9%">相关操作编码</th><th style="width:12%">相关操作名称</th><th style="width:8%">分值 ▸</th></tr>';
			}else{
		th.innerHTML='<tr><th style="width:3%">DIP编码</th><th style="width:23%">主要诊断</th><th style="width:23%">主手术操作</th><th style="width:16%">相关手术</th><th style="width:12%">病种类型</th><th style="width:13%">分值</th></tr>';
		}
		}
	document.getElementById('bd').innerHTML=show.map(function(d){return _dipRenderRow(d,isProv)}).join('');setTimeout(function(){var tbl=document.querySelector('#t-dip table');if(tbl)_makeResizable(tbl)},200)}

document.addEventListener('click',function(e){var ids=['ds','d2s','ps','p2s','dip-ds','dip-d2s','dip-ps','dip-p2s'];ids.forEach(function(id){if(!e.target.closest('#'+id.replace('s',''))&&!e.target.closest('#'+id))document.getElementById(id).style.display='none'})});
function _makeResizable(tbl){
	tbl.querySelectorAll('th').forEach(function(th,i){
	if(th.querySelector('.rh'))return;
	var tid=tbl.closest('.tab');var dipTag=tbl.closest('#t-dip')?'_dip_'+(window._dipActiveTab||'core'):'';var key=tid?'cw_'+tid.id+dipTag:'';
	if(key)try{var saved=JSON.parse(localStorage.getItem(key));if(saved&&saved[i])th.style.width=saved[i]+'px'}catch(e){}
	var rh=document.createElement('div');rh.className='rh';th.appendChild(rh);var sx,sw;
	rh.addEventListener('mousedown',function(e){sx=e.clientX;sw=th.offsetWidth;rh.classList.add('active');document.body.style.cursor='col-resize';
	function mv(ev){var w=sw+(ev.clientX-sx);if(w>60)th.style.width=w+'px'}
	function up(){rh.classList.remove('active');document.body.style.cursor='';document.removeEventListener('mousemove',mv);document.removeEventListener('mouseup',up);
	try{var wd={};tbl.querySelectorAll('th').forEach(function(h,j){if(h.style.width)wd[j]=parseInt(h.style.width)});if(key)localStorage.setItem(key,JSON.stringify(wd))}catch(e){}}
	document.addEventListener('mousemove',mv);document.addEventListener('mouseup',up)})
	})}
setTimeout(function(){document.querySelectorAll('table').forEach(function(tbl){_makeResizable(tbl)})},1000);
