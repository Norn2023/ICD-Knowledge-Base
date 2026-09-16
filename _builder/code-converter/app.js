// ICD Coding Converter - 病案首页→医保结算清单
var _icd10=null,_icd9=null,_dxIdx=1,_procIdx=1,_ventIdx=0,_ecmoIdx=0,_crrtIdx=0;
var _icd10Keys=[],_icd9Keys=[];
var _activeSug=null;
var _drgMeta=null,_mccSet=null,_ccSet=null,_noDxSet=null,_noPxSet=null,_exclInv=null;
var _insExclSet=null;  // Insurance-excluded procedure codes
var _procClass=null;  // Procedure classification (category, entry_option)
var _convertTimer=null;  // Debounce timer for real-time conversion

// ===== REAL-TIME AUTO CONVERSION =====
function _scheduleConvert(){
  clearTimeout(_convertTimer);
  var statusEl=document.getElementById('autoStatus');
  if(statusEl){statusEl.style.display='inline';}
  _convertTimer=setTimeout(function(){
    if(statusEl){statusEl.style.display='none';}
    _convert();
  }, 600);
}

// Load DRG metadata (MCC/CC/排除/no_dx/no_px)
fetch('drg_meta.json').then(r=>r.json()).then(d=>{
  _drgMeta=d;
  _mccSet=new Set(d.mcc);_ccSet=new Set(d.cc);
  _noDxSet=new Set(d.no_dx);_noPxSet=new Set(d.no_px);
  _exclInv=d.excl_inv;
  console.log('DRG meta loaded: mcc='+d.mcc.length+' cc='+d.cc.length+' no_dx='+d.no_dx.length+' no_px='+d.no_px.length);
});

// Load insurance-excluded procedure codes
fetch('insurance_excluded.json').then(r=>r.json()).then(d=>{
  _insExclSet=new Set(d.codes);
  console.log('Insurance excluded codes loaded: '+d.codes.length);
});

// Load procedure classification (category + entry option)
fetch('proc_classification.json').then(r=>r.json()).then(d=>{
  _procClass=d;
  console.log('Procedure classification loaded: '+Object.keys(d).length+' codes');
});

// Add DRG metadata tags to a code result
function _addMetaTags(code, isProc){
  var tags=[];
  if(!_drgMeta)return tags;
  if(!isProc){
    if(_mccSet.has(code))tags.push({cls:'tag-err',t:'MCC'});
    else if(_ccSet.has(code))tags.push({cls:'tag-warn',t:'CC'});
    if(_exclInv&&_exclInv[code]){
      var tbls=_exclInv[code];
      for(var t=0;t<tbls.length;t++)tags.push({cls:'tag-info',t:'✕'+tbls[t].replace('表 ','')});
    }
    if(_noDxSet.has(code))tags.push({cls:'tag-err',t:'不作主诊'});
  }else{
    if(_noPxSet.has(code))tags.push({cls:'tag-err',t:'不作主手术'});
    // Check if code is excluded from insurance settlement list
    if(_insExclSet&&_insExclSet.has(code))tags.push({cls:'tag-err',t:'医保不能填报'});
  }
  return tags;
}

// ===== AGE CALCULATION =====
function _calcAge(){
  var bd=document.getElementById('birthDate').value;
  if(!bd)return;
  var birth=new Date(bd);
  var admStr=document.getElementById('admDate').value;
  var now=admStr?new Date(admStr):new Date();
  var ageYears=now.getFullYear()-birth.getFullYear();
  var m=now.getMonth()-birth.getMonth();
  if(m<0||(m===0&&now.getDate()<birth.getDate()))ageYears--;
  var prevBday=new Date(now.getFullYear(),birth.getMonth(),birth.getDate());
  if(prevBday>now)prevBday=new Date(now.getFullYear()-1,birth.getMonth(),birth.getDate());
  var ageDays=Math.floor((now-prevBday)/(1000*60*60*24));
  document.getElementById('ageDisplay').textContent=ageYears+'岁'+ageDays+'天';
  document.getElementById('ageDays').value=ageYears*365+ageDays;
}

// ===== STAY CALCULATION (计入不计出) =====
function _calcStay(){
  var adm=document.getElementById('admDate').value;
  var dis=document.getElementById('disDate').value;
  if(!adm||!dis)return;
  _admDateVal=new Date(adm);
  _calcAge();
  var admDate=new Date(adm),disDate=new Date(dis);
  var diffMs=disDate-admDate;
  var days=Math.floor(diffMs/(1000*60*60*24));
  document.getElementById('stayDays').textContent=days+'天';
}

// ===== VENTILATOR =====
function _addVent(){
  var list=document.getElementById('ventList');
  var div=document.createElement('div');div.className='time-row';
  div.innerHTML='<select onchange=\"_calcVent();_scheduleConvert()\"><option value=\"invasive\">有创呼吸机</option><option value=\"noninvasive\">无创呼吸机</option></select>'+
    '<span class=\"time-label\">开始:</span><input type=\"text\" placeholder=\"2025-06-15T08:00\" onchange=\"_calcVent();_scheduleConvert()\">'+
    '<span class=\"time-label\">停止:</span><input type=\"text\" placeholder=\"2025-06-22T10:00\" onchange=\"_calcVent();_scheduleConvert()\">'+
    '<button onclick=\"_removeRow(this);_calcVent();_scheduleConvert()\">✕</button>';
  list.appendChild(div);_ventIdx++;_calcVent();
}
function _calcVent(){
  var rows=document.querySelectorAll('#ventList .time-row');
  var totalMin=0,invCount=0,nonCount=0;
  rows.forEach(function(r){
    var sel=r.querySelector('select');var inps=r.querySelectorAll('input[type=text]');
    var start=inps[0].value,end=inps[1].value;
    if(start&&end){var m=(new Date(end)-new Date(start))/(1000*60);if(m>0)totalMin+=m}
    if(sel&&sel.value==='invasive')invCount++;else nonCount++;
  });
  var h=Math.floor(totalMin/60),m=Math.round(totalMin%60);
  document.getElementById('ventTotal').textContent=(h>0||m>0)?(h+'小时'+m+'分 | 有创'+invCount+'次 无创'+nonCount+'次'):'—';
}

// ===== ECMO =====
function _addEcmo(){
  var list=document.getElementById('ecmoList');
  var div=document.createElement('div');div.className='time-row';
  div.innerHTML='<span class=\"time-label\">ECMO</span>'+
    '<span class=\"time-label\">开始:</span><input type=\"text\" placeholder=\"2025-06-20T14:00\" onchange=\"_calcEcmo();_scheduleConvert()\">'+
    '<span class=\"time-label\">停止:</span><input type=\"text\" placeholder=\"2025-06-27T14:00\" onchange=\"_calcEcmo();_scheduleConvert()\">'+
    '<button onclick=\"_removeRow(this);_calcEcmo();_scheduleConvert()\">✕</button>';
  list.appendChild(div);_ecmoIdx++;_calcEcmo();
}
function _calcEcmo(){
  var rows=document.querySelectorAll('#ecmoList .time-row');
  var totalMin=0;
  rows.forEach(function(r){
    var inps=r.querySelectorAll('input[type=text]');
    var start=inps[0].value,end=inps[1].value;
    if(start&&end){var m=(new Date(end)-new Date(start))/(1000*60);if(m>0)totalMin+=m}
  });
  var h=Math.floor(totalMin/60),m=Math.round(totalMin%60);
  document.getElementById('ecmoTotal').textContent=(h>0||m>0)?(h+'小时'+m+'分 | 共'+rows.length+'次'):'—';
}

// ===== CRRT =====
function _addCrrt(){
  var list=document.getElementById('crrtList');
  var div=document.createElement('div');div.className='time-row';
  div.innerHTML='<span class=\"time-label\">CRRT</span>'+
    '<span class=\"time-label\">开始:</span><input type=\"text\" placeholder=\"2025-06-20T09:00\" onchange=\"_calcCrrt();_scheduleConvert()\">'+
    '<span class=\"time-label\">停止:</span><input type=\"text\" placeholder=\"2025-06-21T09:00\" onchange=\"_calcCrrt();_scheduleConvert()\">'+
    '<button onclick=\"_removeRow(this);_calcCrrt();_scheduleConvert()\">✕</button>';
  list.appendChild(div);_crrtIdx++;_calcCrrt();
}
function _calcCrrt(){
  var rows=document.querySelectorAll('#crrtList .time-row');
  var totalMin=0;
  rows.forEach(function(r){
    var inps=r.querySelectorAll('input[type=text]');
    var start=inps[0].value,end=inps[1].value;
    if(start&&end){var m=(new Date(end)-new Date(start))/(1000*60);if(m>0)totalMin+=m}
  });
  var h=Math.floor(totalMin/60),m=Math.round(totalMin%60);
  document.getElementById('crrtTotal').textContent=(h>0||m>0)?(h+'小时'+m+'分 | 共'+rows.length+'次'):'—';
}

function _removeRow(btn){btn.parentElement.remove();}

// ===== NEWBORN WEIGHT TOGGLE =====
function _nbwToggle(){
  var sel=document.getElementById('nbwSelect').value;
  document.getElementById('nbwCustom').style.display=sel==='custom'?'block':'none';
}

// Load mappings
fetch('icd10_map.json').then(r=>r.json()).then(d=>{
  _icd10=d;_icd10Keys=Object.keys(d);
  console.log('ICD10 loaded:',_icd10Keys.length);
});
fetch('icd9_map.json').then(r=>r.json()).then(d=>{
  _icd9=d;_icd9Keys=Object.keys(d);
  console.log('ICD9 loaded:',_icd9Keys.length);
});

// Search dict matching ICD-10 page behavior (scan ALL entries, return ALL matches)
function _searchDict(dict, keys, query){
  if(!dict||!keys)return[];
  var q=query.trim(),lo=q.toLowerCase(),results=[],seen={};
  for(var i=0;i<keys.length;i++){
    var k=keys[i],v=dict[k];
    if(!q||k.toLowerCase().indexOf(lo)>=0||v.name.indexOf(q)>=0||v.name.toLowerCase().indexOf(lo)>=0){
      if(!seen[k]){seen[k]=true;results.push({code:k,name:v.name,entry:v,match:k===q?'exact':'fuzzy'});}
    }
  }
  return results;
}

// Show suggestion dropdown
function _showSug(inputEl, results, nameFieldId, mapFieldId, isProc){
  _hideSug();
  if(!results.length){_activeSug=null;return;}
  // Limit to 50 results for performance
  if(results.length>50){results=results.slice(0,50);}
  var rect=inputEl.getBoundingClientRect();
  var div=document.createElement('div');div.className='code-sug';div.id='_sugDd';
  div.style.cssText='position:fixed;z-index:9999;left:'+rect.left+'px;top:'+(rect.bottom+2)+'px;width:'+Math.max(rect.width,380)+'px;max-height:420px;overflow:auto;background:var(--bg2);border:1px solid var(--border);border-radius:var(--r);box-shadow:0 4px 16px rgba(0,0,0,.12);font-size:.8em';
  for(var i=0;i<results.length;i++){
    var r=results[i];var item=document.createElement('div');
    item.style.cssText='padding:8px 12px;cursor:pointer;border-bottom:1px solid var(--border);display:flex;gap:10px;align-items:flex-start';
    var metaTags=_addMetaTags(r.code,isProc);
    var tagsHtml=metaTags.map(function(m){return '<span class=\"tag '+m.cls+'\">'+m.t+'</span>';}).join('');
    item.innerHTML='<span style=\"font-weight:600;color:var(--accent);white-space:nowrap;min-width:90px\">'+r.code+'</span><span style=\"flex:1\">'+r.name+'</span>'+tagsHtml+'<span style=\"font-size:.7em;color:var(--text2);white-space:nowrap;margin-left:4px\">'+(r.match==='exact'?'精确':'模糊')+'</span>';
    (function(res, nf, mf, inp){
      item.addEventListener('click',function(e){e.stopPropagation();_selectSug(res,nf,mf,inp);});
      item.addEventListener('mousedown',function(e){e.preventDefault();});
    })(r, nameFieldId, mapFieldId, inputEl);
    div.appendChild(item);
  }
  document.body.appendChild(div);
  _activeSug={div:div,input:inputEl,nameField:nameFieldId,mapField:mapFieldId,results:results};
  // Close on outside click
  setTimeout(function(){
    document.addEventListener('click',_hideSug,{once:true});
  },50);
}

function _hideSug(){
  if(_activeSug&&_activeSug.div){_activeSug.div.remove();_activeSug=null;}
}

function _selectSug(result, nameFieldId, mapFieldId, inputEl){
  _hideSug();
  var nameField=document.getElementById(nameFieldId);
  var mapField=document.getElementById(mapFieldId);
  inputEl.value=result.code;
  nameField.value=result.name;
  mapField.value=JSON.stringify(result.entry);
  nameField.style.borderColor='var(--success)';
}

// Lookup ICD10 diagnosis code/name
var _dxCodeTimer=null,_procCodeTimer=null;

function _lookupDx(inpEl,nameEl,mapEl){
  var inp=(typeof inpEl==='string'?document.getElementById(inpEl):inpEl);
  var query=inp.value.trim();
  var nameField=typeof nameEl==='string'?document.getElementById(nameEl):document.getElementById(nameEl);
  var mapField=typeof mapEl==='string'?document.getElementById(mapEl):document.getElementById(mapEl);
  if(!query||!_icd10){clearTimeout(_dxCodeTimer);_hideSug();return;}

  clearTimeout(_dxCodeTimer);
  _dxCodeTimer=setTimeout(function(){
  var results=_searchDict(_icd10,_icd10Keys,query,15);
  if(results.length===1&&results[0].match==='exact'){
    // Single exact match - auto-fill
    nameField.value=results[0].name;
    mapField.value=JSON.stringify(results[0].entry);
    nameField.style.borderColor='var(--success)';
    _hideSug();
    _scheduleConvert();  // Real-time: auto convert on exact match
  }else if(results.length>0){
    // Show suggestions
    _showSug(inp,results,nameEl,mapEl,false);
  }else{
    nameField.value='未找到匹配编码';
    nameField.style.borderColor='var(--danger)';
    mapField.value='';
    _hideSug();
  }
  },200);
}

// Lookup ICD9 procedure code/name
function _lookupProc(inpEl,nameEl,mapEl){
  var inp=(typeof inpEl==='string'?document.getElementById(inpEl):inpEl);
  var query=inp.value.trim();
  var nameField=typeof nameEl==='string'?document.getElementById(nameEl):document.getElementById(nameEl);
  var mapField=typeof mapEl==='string'?document.getElementById(mapEl):document.getElementById(mapEl);
  if(!query||!_icd9){clearTimeout(_procCodeTimer);_hideSug();return;}

  clearTimeout(_procCodeTimer);
  _procCodeTimer=setTimeout(function(){

  // Try format normalization for ICD9
  var queries=[query];
  var parts=query.split('.');
  if(parts.length===1&&query.length>2){queries.push(query.substring(0,2)+'.'+query.substring(2));}

  var allResults=[];
  for(var q=0;q<queries.length;q++){
    var results=_searchDict(_icd9,_icd9Keys,queries[q]);
    for(var r=0;r<results.length;r++){
      if(!allResults.some(function(x){return x.code===results[r].code})){
        allResults.push(results[r]);
      }
    }
  }

  if(allResults.length===1&&allResults[0].match==='exact'){
    nameField.value=allResults[0].name;
    mapField.value=JSON.stringify(allResults[0].entry);
    nameField.style.borderColor='var(--success)';
    _hideSug();
    _scheduleConvert();  // Real-time: auto convert on exact match
  }else if(allResults.length>0){
    _showSug(inp,allResults,nameEl,mapEl,true);
  }else{
    nameField.value='未找到匹配编码';
    nameField.style.borderColor='var(--danger)';
    mapField.value='';
    _hideSug();
  }
  },200);
}

// Lookup by diagnosis NAME (keyword search)
var _dxNameTimer=null,_procNameTimer=null;

function _lookupDxName(inpEl,codeEl,mapEl){
  var inp=(typeof inpEl==='string'?document.getElementById(inpEl):inpEl);
  var query=inp.value.trim();
  var codeField=typeof codeEl==='string'?document.getElementById(codeEl):(codeEl.dataset?document.getElementById(codeEl.dataset.codeId):null);
  if(!codeField)codeField=document.getElementById(codeEl);
  var mapField=typeof mapEl==='string'?document.getElementById(mapEl):document.getElementById(mapEl);
  if(!query||!_icd10){clearTimeout(_dxNameTimer);_hideSug();return;}

  clearTimeout(_dxNameTimer);
  _dxNameTimer=setTimeout(function(){
  var results=_searchDict(_icd10,_icd10Keys,query,15);
  if(results.length===1){
    inp.value=results[0].name;codeField.value=results[0].code;
    mapField.value=JSON.stringify(results[0].entry);
    inp.style.borderColor='var(--success)';_hideSug();
  }else if(results.length>0){
    _showSug(inp,results,codeEl,mapEl,false);
  }else{_hideSug();}
  },300);
}

// Lookup by procedure NAME (keyword search)
function _lookupProcName(inpEl,codeEl,mapEl){
  var inp=(typeof inpEl==='string'?document.getElementById(inpEl):inpEl);
  var query=inp.value.trim();
  var codeField=typeof codeEl==='string'?document.getElementById(codeEl):(codeEl.dataset?document.getElementById(codeEl.dataset.codeId):null);
  if(!codeField)codeField=document.getElementById(codeEl);
  var mapField=typeof mapEl==='string'?document.getElementById(mapEl):document.getElementById(mapEl);
  if(!query||!_icd9){clearTimeout(_procNameTimer);_hideSug();return;}

  clearTimeout(_procNameTimer);
  _procNameTimer=setTimeout(function(){
  var results=_searchDict(_icd9,_icd9Keys,query,15);
  if(results.length===1){
    inp.value=results[0].name;codeField.value=results[0].code;
    mapField.value=JSON.stringify(results[0].entry);
    inp.style.borderColor='var(--success)';_hideSug();
  }else if(results.length>0){
    _showSug(inp,results,codeEl,mapEl,true);
  }else{_hideSug();}
  },300);
}

// Update selectSug to correctly fill code←code, name←name
var _origSelectSug=_selectSug;
_selectSug=function(result, targetFieldId, mapFieldId, inputEl){
  var targetField=document.getElementById(targetFieldId);
  var mapField=document.getElementById(mapFieldId);
  // Determine which field is code and which is name
  var codeField, nameField;
  if(inputEl.classList.contains('code-inp')||(inputEl.id&&inputEl.id.indexOf('Code')>=0)){
    // User typed in code field
    codeField=inputEl;nameField=targetField;
  }else{
    // User typed in name field - targetFieldId points to the code field
    codeField=targetField;nameField=inputEl;
  }
  codeField.value=result.code;codeField.style.borderColor='var(--success)';
  nameField.value=result.name;nameField.style.borderColor='var(--success)';
  mapField.value=JSON.stringify(result.entry);
  _hideSug();
  _scheduleConvert();  // Real-time: auto convert after selection
};

// Add other diagnosis row
function _addDx(){
  var container=document.getElementById('otherDxList');
  var div=document.createElement('div');div.className='dx-row';
  var cid='dxCode'+_dxIdx;
  div.innerHTML='<input class="code-inp" id="'+cid+'" placeholder="编码" oninput="_lookupDx(this,\'dxName'+_dxIdx+'\',\'dxMap'+_dxIdx+'\');_scheduleConvert()" data-idx="'+_dxIdx+'">'+
    '<input id="dxName'+_dxIdx+'" placeholder="诊断名称（可输入关键字搜索）" style="flex:1" oninput="_lookupDxName(this,\''+cid+'\',\'dxMap'+_dxIdx+'\');_scheduleConvert()" data-idx="'+_dxIdx+'" data-code-id="'+cid+'">'+
    '<input type="hidden" id="dxMap'+_dxIdx+'">'+
    '<button onclick="_removeDx(this)">✕</button>';
  container.appendChild(div);_dxIdx++;
}

// Remove diagnosis row
function _removeDx(btn){
  var rows=document.getElementById('otherDxList').children;
  if(rows.length<=1)return;
  btn.parentElement.remove();
  _scheduleConvert();  // Real-time: auto convert after removal
}

// Add other procedure row
function _addProc(){
  var container=document.getElementById('otherProcList');
  var div=document.createElement('div');div.className='dx-row';
  var pid='procCode'+_procIdx;
  div.innerHTML='<input class="code-inp" id="'+pid+'" placeholder="编码" oninput="_lookupProc(this,\'procName'+_procIdx+'\',\'procMap'+_procIdx+'\');_scheduleConvert()" data-idx="'+_procIdx+'">'+
    '<input id="procName'+_procIdx+'" placeholder="手术名称（可输入关键字搜索）" style="flex:1" oninput="_lookupProcName(this,\''+pid+'\',\'procMap'+_procIdx+'\');_scheduleConvert()" data-idx="'+_procIdx+'" data-code-id="'+pid+'">'+
    '<input type="hidden" id="procMap'+_procIdx+'">'+
    '<button onclick="_removeProc(this)">✕</button>';
  container.appendChild(div);_procIdx++;
}

// Remove procedure row
function _removeProc(btn){
  var rows=document.getElementById('otherProcList').children;
  if(rows.length<=1)return;
  btn.parentElement.remove();
  _scheduleConvert();  // Real-time: auto convert after removal
}

// Procedure category priority order for insurance settlement list
var _procCatOrder={'手术':1,'介入治疗':2,'治疗性操作':3,'诊断性操作':4,'':99};

function _getProcCat(code){
  if(_procClass&&_procClass[code])return _procClass[code].category||'';
  return '';
}

// Sort procedures by category priority (surgery > interventional > therapeutic > diagnostic)
function _sortByCat(a,b){
  var ca=_procCatOrder[_getProcCat(a.code)]||99;
  var cb=_procCatOrder[_getProcCat(b.code)]||99;
  return ca-cb;
}

// Main conversion
function _convert(){
  console.log('_convert START');
  try {
  if(!_icd10||!_icd9){
    document.getElementById('warnings').innerHTML='<div class="warning-box"><b>Error</b>: ICD data not loaded, please refresh</div>';
    document.getElementById('result').style.display='block';
    document.getElementById('emptyState').style.display='none';
    return;
  }
  console.log('_convert: icd10='+_icd10Keys.length+' keys, icd9='+_icd9Keys.length+' keys, drgMeta='+(_drgMeta?'loaded':'null'));
  var warnings=[],rules=[];
  var ageDays=parseInt(document.getElementById('ageDays').value)||0;
  var age=Math.floor(ageDays/365);
  var gender=document.getElementById('gender').value;
  var admType=document.getElementById('admType').value;

  // Admission type conversion: 病案首页(5种) → 医保结算清单(4种)
  var admMap={'1':'1-急诊','2':'2-门诊','3':'3-其他医疗机构转入','4':'3-其他医疗机构转入','9':'9-其他'};
  var admInsCode=admMap[admType]||admType;
  if(admType!=='1'&&admType!=='2'){
    rules.push('入院途径：病案首页编码'+admType+' → 医保结算清单编码'+admInsCode);
  }

  // Collect all diagnoses
  function getDxData(codeId,nameId,mapId){
    var code=document.getElementById(codeId).value.trim().toUpperCase();
    var name=document.getElementById(nameId).value.trim();
    var mapRaw=document.getElementById(mapId).value;
    var entry=mapRaw?JSON.parse(mapRaw):(_icd10[code]||null);
    return {code:code,name:name,entry:entry,insCode:entry?entry.ins_code:'',insName:entry?entry.ins_name:''};
  }

  var mainDx=getDxData('mainDxCode','mainDxName','mainDxMap');
  var otherDxs=[];
  for(var i=0;i<_dxIdx;i++){
    var codeEl=document.getElementById('dxName'+i);
    if(!codeEl)continue;
    var row=codeEl.closest('.dx-row');
    if(!row)continue;
    var codeInp=row.querySelector('.code-inp');
    var nameInp=row.querySelector('input[type="text"]');
    var mapInp=row.querySelector('input[type="hidden"]');
    if(!codeInp||!codeInp.value.trim())continue;
    var code=codeInp.value.trim().toUpperCase();
    var name=nameInp?nameInp.value.trim():'';
    var mapRaw=mapInp?mapInp.value:'';
    var entry=mapRaw?JSON.parse(mapRaw):(_icd10[code]||null);
    if(code){
      otherDxs.push({code:code,name:name||(entry?entry.name:''),entry:entry,insCode:entry?entry.ins_code:'',insName:entry?entry.ins_name:'',status:'keep'});
    }
  }

  // Collect all procedures
  function getProcData(codeId,nameId,mapId){
    var code=document.getElementById(codeId).value.trim();
    var name=document.getElementById(nameId).value.trim();
    var mapRaw=document.getElementById(mapId).value;
    var entry=mapRaw?JSON.parse(mapRaw):(_icd9[code]||null);
    if(!entry&&code){
      var parts=code.split('.');
      if(parts.length===1&&code.length>2){
        var withDot=code.substring(0,2)+'.'+code.substring(2);
        entry=_icd9[withDot];
      }
    }
    return {code:code,name:name,entry:entry,insCode:entry?entry.ins_code:'',insName:entry?entry.ins_name:''};
  }

  var mainProc=getProcData('mainProcCode','mainProcName','mainProcMap');
  var otherProcs=[];
  for(var j=0;j<_procIdx;j++){
    var codeEl2=document.getElementById('procName'+j);
    if(!codeEl2)continue;
    var row2=codeEl2.closest('.dx-row');
    if(!row2)continue;
    var codeInp2=row2.querySelector('.code-inp');
    var nameInp2=row2.querySelector('input[type="text"]');
    var mapInp2=row2.querySelector('input[type="hidden"]');
    if(!codeInp2||!codeInp2.value.trim())continue;
    var code2=codeInp2.value.trim();
    var name2=nameInp2?nameInp2.value.trim():'';
    var mapRaw2=mapInp2?mapInp2.value:"";
    var entry2=mapRaw2?JSON.parse(mapRaw2):null;
    if(!entry2&&code2&&_icd9){
      entry2=_icd9[code2];
      if(!entry2){
        var p2=code2.split('.');if(p2.length===1&&code2.length>2){entry2=_icd9[code2.substring(0,2)+'.'+code2.substring(2)];}
      }
    }
    if(code2){
      otherProcs.push({code:code2,name:name2||(entry2?entry2.name:''),entry:entry2,insCode:entry2?entry2.ins_code:'',insName:entry2?entry2.ins_name:''});
    }
  }

  // Sort other procedures by category priority (医保结算清单: 手术>介入>治疗>诊断)
  otherProcs.sort(_sortByCat);
  if(otherProcs.length>1){
    var catNames=otherProcs.map(function(p){return _getProcCat(p.code)||'未分类';});
    var uniqueCats=catNames.filter(function(v,i,a){return a.indexOf(v)===i;});
    if(uniqueCats.length>1){
      rules.push('手术操作已按医保结算清单优先级重排：手术→介入治疗→治疗性操作→诊断性操作');
    }
  }

  // === RULE 1: Main diagnosis validation ===
  if(!mainDx.code){
    warnings.push({type:'error',text:'主要诊断为必填项，请输入病案首页主要诊断编码'});
  }

  // === RULE 2: Tumor chemo/radiotherapy Z51 priority ===
  if(mainDx.code&&(mainDx.code.startsWith('C')||mainDx.code.startsWith('D0')||mainDx.code.startsWith('D1')||mainDx.code.startsWith('D2')||mainDx.code.startsWith('D3'))){
    var hasChemo=false,hasRadio=false;
    for(var k=0;k<otherDxs.length;k++){
      var d=otherDxs[k];
      if(d.code.startsWith('Z51.0'))hasRadio=true;
      if(d.code.startsWith('Z51.1'))hasChemo=true;
      if(d.code.startsWith('Z51.2'))hasChemo=true;
    }
    if(hasChemo||hasRadio){
      var txType=hasChemo?'化学治疗':'放射治疗';
      warnings.push({type:'warn',text:'肿瘤患者本次入院行'+txType+'——医保结算清单主要诊断建议优先选择 Z51.x（'+txType+'）作为主要诊断，原肿瘤编码作为其他诊断'});
      if(hasChemo)rules.push('肿瘤化疗→主要诊断建议Z51.1/Z51.2');
      if(hasRadio)rules.push('肿瘤放疗→主要诊断建议Z51.0');
    }
  }

  // === RULE 3: Obstetric delivery coding priority ===
  if(mainDx.code&&mainDx.code.startsWith('O')){
    if(mainDx.code>='O80'&&mainDx.code<='O84'){
      rules.push('产科分娩：O80-O84编码为医保清单优先编码');
    }
    if(mainDx.code>='O10'&&mainDx.code<='O99'&&!(mainDx.code>='O80'&&mainDx.code<='O84')){
      warnings.push({type:'warn',text:'产科诊断：医保结算清单要求分娩编码(O80-O84)优先作为主要诊断，产褥并发症作为其他诊断（当前主诊断为'+mainDx.code+'）'});
    }
  }

  // === RULE 4: Remove suspected diagnoses ===
  var removedDxs=[];
  var filteredOtherDxs=[];
  for(var m=0;m<otherDxs.length;m++){
    var od=otherDxs[m];
    var nameLC=(od.name||'').toLowerCase();
    if(nameLC.indexOf('待查')>=0||nameLC.indexOf('疑似')>=0||nameLC.indexOf('待排')>=0||nameLC.indexOf('?')>=0||nameLC.indexOf('可能')>=0){
      od.status='removed_suspect';
      removedDxs.push(od);
    }else{
      filteredOtherDxs.push(od);
    }
  }
  if(removedDxs.length>0){
    warnings.push({type:'warn',text:'已移除 '+removedDxs.length+' 条疑似/待查诊断（医保清单不得填写疑似诊断）：'+removedDxs.map(function(x){return x.code+' '+x.name;}).join('；')});
    rules.push('疑似/待查诊断不得填入医保结算清单');
  }

  // === RULE 5: Check for post-op complications ===
  for(var n=0;n<filteredOtherDxs.length;n++){
    var od2=filteredOtherDxs[n];
    if(od2.code.startsWith('T81')||od2.code.startsWith('T80')){
      warnings.push({type:'error',text:'术后并发症编码('+od2.code+' '+od2.name+')——医保审核重点监控，须确认是否为医疗质量问题导致，可能影响DRG支付'});
    }
  }

  // === RULE 6: Code mapping differences ===
  var mapDiffs=[];
  if(mainDx.code&&mainDx.insCode&&mainDx.code!==mainDx.insCode){
    mapDiffs.push('主要诊断：国临版 '+mainDx.code+' → 医保版 '+mainDx.insCode);
  }
  for(var p=0;p<filteredOtherDxs.length;p++){
    var od3=filteredOtherDxs[p];
    if(od3.code&&od3.insCode&&od3.code!==od3.insCode){
      mapDiffs.push('其他诊断 '+od3.code+' → '+od3.insCode);
    }
  }
  if(mainProc.code&&mainProc.insCode&&mainProc.code!==mainProc.insCode){
    mapDiffs.push('主要手术：国临版 '+mainProc.code+' → 医保版 '+mainProc.insCode);
  }
  for(var q=0;q<otherProcs.length;q++){
    var op=otherProcs[q];
    if(op.code&&op.insCode&&op.code!==op.insCode){
      mapDiffs.push('其他手术 '+op.code+' → '+op.insCode);
    }
  }
  if(mapDiffs.length>0){
    rules.push('编码映射差异（'+mapDiffs.length+'处）：'+mapDiffs.join('；'));
  }

  // === RULE 7: Ventilator/ECMO/CRRT time warnings ===
  var ventTotal=document.getElementById('ventTotal').textContent;
  var ecmoTotal=document.getElementById('ecmoTotal').textContent;
  var crrtTotal=document.getElementById('crrtTotal').textContent;
  if(ventTotal&&ventTotal!=='—'){
    var ventRows=document.querySelectorAll('#ventList .time-row');
    ventRows.forEach(function(r){
      var sel=r.querySelector('select');
      if(sel&&sel.value==='invasive'){
        var inps=r.querySelectorAll('input');var s=inps[0].value,e=inps[1].value;
        if(s&&e){var h=Math.floor((new Date(e)-new Date(s))/(1000*60*60));
          if(h>=96){warnings.push({type:'warn',text:'有创呼吸机使用≥96小时（'+h+'h）→ DRG分组：AH2有创呼吸机支持≥96h'});}
        }
      }
    });
  }
  if(ecmoTotal&&ecmoTotal!=='—'){warnings.push({type:'warn',text:'ECMO使用记录 → 高资源消耗技术，DRG单独分组（如AH1 ECMO支持）'});}
  if(crrtTotal&&crrtTotal!=='—'){warnings.push({type:'warn',text:'CRRT使用记录 → 影响DRG分组（部分ADRG组有CRRT加成）'});}

  // === RULE 8: Discharge type warning ===
  var disTypeVal=document.getElementById('disType').value;
  if(disTypeVal==='4'){warnings.push({type:'error',text:'离院方式为"非医嘱离院"——医保可能拒付或大幅扣减，需记录具体原因'});}
  else if(disTypeVal==='5'){warnings.push({type:'warn',text:'离院方式为"死亡"——死亡病例单独分析，部分DRG权重上调，但须确保主要诊断与死亡原因一致'});}

  // === RULE 9: Insurance-excluded procedures ===
  var exclProcs=[];
  if(mainProc.code&&_insExclSet&&_insExclSet.has(mainProc.code)){
    exclProcs.push('主要手术 '+mainProc.code+' '+mainProc.name);
  }
  for(var ep=0;ep<otherProcs.length;ep++){
    if(_insExclSet&&_insExclSet.has(otherProcs[ep].code)){
      exclProcs.push('其他手术 '+otherProcs[ep].code+' '+otherProcs[ep].name);
    }
  }
  if(exclProcs.length>0){
    warnings.push({type:'error',text:'以下手术操作编码不在CHS-DRG 2.0手术ADRG范围内，医保结算清单不能填报：'+exclProcs.join('；')});
    rules.push('非DRG入组编码：'+exclProcs.length+'条编码不在医保结算清单填报范围');
  }

  // === RENDER RESULTS (card-style matching left input) ===
  var html='';

  // Warnings
  if(warnings.length>0){
    html+='<div class="warning-box"><b>审核预警 ('+warnings.length+'条)</b>';
    for(var w=0;w<warnings.length;w++){
      html+='<div class="warning-item">'+warnings[w].text+'</div>';
    }
    html+='</div>';
  }
  document.getElementById('warnings').innerHTML=html;

  // Rules applied
  if(rules.length>0){
    var rh='<div class="rule-box"><b>已应用转换规则 ('+rules.length+'条)</b>';
    for(var rl=0;rl<rules.length;rl++){
      rh+='<div class="warning-item" style="border-left-color:var(--accent2)">'+rules[rl]+'</div>';
    }
    rh+='</div>';
    document.getElementById('rulesApplied').innerHTML=rh;
  }else{
    document.getElementById('rulesApplied').innerHTML='';
  }

  // Main diagnosis
  var mainDxInsCode=mainDx.insCode||mainDx.code;
  if(!mainDx.code){
    document.getElementById('rx_mainDxCode').value='';
    document.getElementById('rx_mainDxName').value='';
    document.getElementById('rx_mainDxStatus').innerHTML='<span class="tag tag-err">缺失</span>';
  } else {
    document.getElementById('rx_mainDxCode').value=mainDx.code;
    document.getElementById('rx_mainDxName').value=mainDx.name;
    if(mainDx.code===mainDxInsCode){
      document.getElementById('rx_mainDxStatus').innerHTML='<span class="tag tag-ok">编码一致</span>';
    } else {
      document.getElementById('rx_mainDxStatus').innerHTML='<span class="tag tag-warn">转换 '+mainDxInsCode+'</span>';
    }
  }

  // Other diagnoses
  var odHtml='';
  for(var a=0;a<filteredOtherDxs.length;a++){
    var fd=filteredOtherDxs[a];
    var sc='tag-ok',st='保留';
    if(fd.code===fd.insCode){sc='tag-ok';st='编码一致';}
    else if(fd.insCode){sc='tag-warn';st='转换 '+fd.insCode;}
    else{sc='tag-err';st='无映射';}
    odHtml+='<div class="rx-row"><div class="rx-col"><label>编码</label><input readonly value="'+fd.code+'"></div>'+
      '<div class="rx-col"><label>名称</label><input readonly value="'+fd.name+'"></div>'+
      '<div class="rx-col rx-status"><span class="tag '+sc+'">'+st+'</span></div></div>';
  }
  for(var b=0;b<removedDxs.length;b++){
    var rd=removedDxs[b];
    odHtml+='<div class="rx-row" style="opacity:.45;text-decoration:line-through"><div class="rx-col"><label>编码</label><input readonly value="'+rd.code+'"></div>'+
      '<div class="rx-col"><label>名称</label><input readonly value="'+rd.name+'"></div>'+
      '<div class="rx-col rx-status"><span class="tag tag-err">已排除</span></div></div>';
  }
  if(!odHtml) odHtml='<div style="font-size:.82em;color:var(--text2);padding:8px 0">无其他诊断</div>';
  document.getElementById('rx_otherDxList').innerHTML=odHtml;
  var sp=[];
  if(filteredOtherDxs.length>0) sp.push(filteredOtherDxs.length+'条保留');
  if(removedDxs.length>0) sp.push(removedDxs.length+'条已排除');
  document.getElementById('rx_otherDxSummary').textContent=sp.length?'共 '+sp.join('，') : '';

  // Main procedure
  var mainProcInsCode=mainProc.insCode||mainProc.code;
  if(!mainProc.code){
    document.getElementById('rx_mainProcCode').value='';
    document.getElementById('rx_mainProcName').value='';
    document.getElementById('rx_mainProcStatus').innerHTML='<span class="tag tag-err">未填写</span>';
  } else {
    document.getElementById('rx_mainProcCode').value=mainProc.code;
    document.getElementById('rx_mainProcName').value=mainProc.name;
    if(mainProc.code===mainProcInsCode){
      document.getElementById('rx_mainProcStatus').innerHTML='<span class="tag tag-ok">编码一致</span>';
    } else {
      document.getElementById('rx_mainProcStatus').innerHTML='<span class="tag tag-warn">转换 '+mainProcInsCode+'</span>';
    }
  }

  // Other procedures
  var opHtml='';
  for(var c=0;c<otherProcs.length;c++){
    var op2=otherProcs[c];
    var oc='tag-ok',ot='保留';
    if(op2.code===op2.insCode){oc='tag-ok';ot='编码一致';}
    else if(op2.insCode){oc='tag-warn';ot='转换 '+op2.insCode;}
    else{oc='tag-err';ot='无映射';}
    opHtml+='<div class="rx-row"><div class="rx-col"><label>编码</label><input readonly value="'+op2.code+'"></div>'+
      '<div class="rx-col"><label>名称</label><input readonly value="'+op2.name+'"></div>'+
      '<div class="rx-col rx-status"><span class="tag '+oc+'">'+ot+'</span></div></div>';
  }
  if(!opHtml) opHtml='<div style="font-size:.82em;color:var(--text2);padding:8px 0">无其他手术操作</div>';
  document.getElementById('rx_otherProcList').innerHTML=opHtml;
  if(otherProcs.length>0){
    var uc=[];
    otherProcs.forEach(function(p){var c2=_getProcCat(p.code);if(c2&&!uc.includes(c2))uc.push(c2);});
    document.getElementById('rx_otherProcSummary').textContent='共 '+otherProcs.length+' 条，已按医保优先级排序，类别：'+uc.join('、');
  } else {
    document.getElementById('rx_otherProcSummary').textContent='';
  }

  // Special section - summary cards
  var specHtml='';
  var ageDisp=document.getElementById('ageDisplay').textContent;
  if(ageDisp&&ageDisp!=='—') specHtml+='<div class="rx-row"><div class="rx-col"><label>年龄</label><input readonly value="'+ageDisp+'"></div></div>';
  var stay=document.getElementById('stayDays').textContent;
  if(stay&&stay!=='—') specHtml+='<div class="rx-row"><div class="rx-col"><label>住院天数</label><input readonly value="'+stay+'"></div></div>';
  var nbw=document.getElementById('nbwSelect').value;
  var nbwVal=nbw==='custom'?document.getElementById('nbwCustom').value+'g':(nbw||'');
  if(nbwVal) specHtml+='<div class="rx-row"><div class="rx-col"><label>新生儿体重</label><input readonly value="'+nbwVal+'"></div></div>';
  var vt=document.getElementById('ventTotal').textContent;
  if(vt&&vt!=='—') specHtml+='<div class="rx-row"><div class="rx-col"><label>呼吸机</label><input readonly value="'+vt+'"></div></div>';
  var et=document.getElementById('ecmoTotal').textContent;
  if(et&&et!=='—') specHtml+='<div class="rx-row"><div class="rx-col"><label>ECMO</label><input readonly value="'+et+'"></div></div>';
  var ct=document.getElementById('crrtTotal').textContent;
  if(ct&&ct!=='—') specHtml+='<div class="rx-row"><div class="rx-col"><label>CRRT</label><input readonly value="'+ct+'"></div></div>';
  var admT=document.getElementById('admType');
  specHtml+='<div class="rx-row"><div class="rx-col"><label>入院途径</label><input readonly value="'+admT.options[admT.selectedIndex].text+'"></div></div>';
  var disT=document.getElementById('disType');
  specHtml+='<div class="rx-row"><div class="rx-col"><label>离院方式</label><input readonly value="'+disT.options[disT.selectedIndex].text+'"></div></div>';
  document.getElementById('rx_specialList').innerHTML=specHtml;
  document.getElementById('rx_specialSection').style.display=specHtml?'block':'none';



  document.getElementById('emptyState').style.display='none';

  } catch(e) {
    console.error('_convert ERROR:', e);
    document.getElementById('warnings').innerHTML='<div class="warning-box"><b>🔴 JS错误</b>: '+e.message+' (行: '+(e.lineNumber||'?')+')</div>';
    document.getElementById('result').style.display='block';
    document.getElementById('emptyState').style.display='none';
    document.getElementById('rulesApplied').innerHTML='<div class="warning-box"><pre>'+e.stack+'</pre></div>';
  }
}

// Clear all
function _clear(){
  document.getElementById('mainDxCode').value='';
  document.getElementById('mainDxName').value='';
  document.getElementById('mainProcCode').value='';
  document.getElementById('mainProcName').value='';
  document.getElementById('result').style.display='none';
  document.getElementById('emptyState').style.display='block';
}
