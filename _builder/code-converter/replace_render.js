"""Replace rendering section in app.js"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('D:/AI_libra/codex_Obsi/_builder/code-converter/app.js','r',encoding='utf-8') as f:
    content = f.read()

start = content.find("  // === RENDER RESULTS ===")
end_marker = "  // Show result\n  document.getElementById('result').style.display='block';"
end = content.find(end_marker) + len(end_marker)

new_section = '''  // === RENDER RESULTS (card-style matching left input) ===
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
'''

content = content[:start] + new_section + "\n\n" + content[end:]

with open('D:/AI_libra/codex_Obsi/_builder/code-converter/app.js','w',encoding='utf-8') as f:
    f.write(content)

print('Replaced rendering section OK')
PYEOF
