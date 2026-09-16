"""Restructure display: DRG first, then variants, then ADRG, then MDC"""
with open('index.html', 'r', encoding='utf-8') as f:
    c = f.read()

marker = "document.getElementById('drr').innerHTML='<div class=\"clr\"><h3>匹配"
idx = c.find(marker)
if idx < 0: print("ERROR"); exit(1)

end_marker = "</div></div>'\n"
end_idx = c.find(end_marker, idx)
end_idx = c.find("'", end_idx) + 1
if end_idx <= 0: print("ERROR end"); exit(1)

print(f"Replacing {idx} to {end_idx}")

new_display = """document.getElementById('drr').innerHTML='<div class="clr"><h3>匹配 '+tp.length+' 个候选 DRG</h3><div style="font-size:.85em;color:var(--text-dim);margin-bottom:10px">主诊:'+(pd?pd.c+' '+pd.n:'-')+' | 其他诊断:'+_dx2.length+'个 | 主手术:'+(pp?pp.c+' '+pp.n:'-')+' | 其他手术:'+_px2.length+'个</div>'+ng+'<div style="display:flex;flex-direction:column;gap:12px;margin-top:10px">'+tp.map(function(s){var mdc=_drg.adrg_mdc||{},md=mdc[s.adrg]||{};var cond=[];if(pd&&s.dx.has(pd.c))cond.push('<span style="color:var(--success)">主诊 '+pd.c+'</span>');else if(s.dx.size>0)cond.push('<span style="color:var(--warning)">其他诊断</span>');if(pp&&s.px.has(pp.c))cond.push('<span style="color:var(--success)">主手术 '+pp.c+'</span>');else if(s.px.size>0)cond.push('<span style="color:var(--warning)">其他手术</span>');var mccS=_drg.mccS||new Set,ccS=_drg.ccS||new Set,excl=_drg.excl||{},hasMCC=false,hasCC=false,mccDx=[],ccDx=[];_dx2.forEach(function(d){if(mccS.has(d.c)){var ok=true;for(var ek in excl){if(excl[ek].indexOf(d.c)>=0&&ek.indexOf(s.adrg)>=0){ok=false;break}}if(ok){hasMCC=true;mccDx.push(d.c)}}else if(ccS.has(d.c)){var ok2=true;for(var ek2 in excl){if(excl[ek2].indexOf(d.c)>=0&&ek2.indexOf(s.adrg)>=0){ok2=false;break}}if(ok2){hasCC=true;ccDx.push(d.c)}}});if(mccDx.length)cond.push('<span style="color:var(--danger)">MCC: '+mccDx.join(', ')+'</span>');else if(ccDx.length)cond.push('<span style="color:var(--warning)">CC: '+ccDx.join(', ')+'</span>');var effS=hasMCC?'MCC':(hasCC?'CC':'noCC'),matchD=s.drgs[0];for(var j=0;j<s.drgs.length;j++){if(s.drgs[j].s===effS){matchD=s.drgs[j];break}}var isTop=(tp[0].score===s.score);var catClr=md.cat.indexOf('外科')>=0?'var(--danger)':(md.cat.indexOf('内科')>=0?'var(--accent)':'var(--warning)');return'<div style="background:var(--bg);border:1px solid '+(isTop?'var(--accent)':'var(--border)')+';border-radius:var(--r);padding:14px;'+(isTop?'box-shadow:0 0 0 1px var(--accent);':'')+'"><div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap"><b style="font-size:1.15em;color:var(--accent)">'+matchD.c+'</b><span style="color:var(--text-dim)">'+matchD.n+'</span><span style="font-size:.7em;padding:2px 8px;border-radius:10px;background:'+catClr+';color:#fff;font-weight:600">'+md.cat+'</span><span style="font-size:.72em;padding:1px 6px;border-radius:8px;background:var(--accent);color:#fff;font-weight:600">'+s.score+'分</span></div><div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:3px;font-size:.7em;color:var(--text-dim)">所有DRG分组: '+s.drgs.map(function(d){var c2='var(--text-dim)';if(d.s===effS)c2='var(--accent)';return'<span style="padding:1px 6px;border-radius:6px;color:'+c2+';'+(d.s===effS?'font-weight:700;background:rgba(59,125,224,.1)':'')+'">'+d.c+' ['+d.s+']</span>'}).join(' ')+'</div><div style="font-size:.75em;color:var(--text-dim);margin-top:6px;padding-top:6px;border-top:1px dotted var(--border)">ADRG  '+s.adrg+'  '+s.an+'  |  MDC  '+md.mdc+'  '+md.mdc_n+'</div><div style="font-size:.75em;color:var(--text-dim);margin-top:4px">入组条件: '+md.cond+(md.rem?', '+md.rem:'')+'</div><div style="font-size:.75em;margin-top:3px">本次匹配: '+cond.join(' | ')+'</div></div>'}).join('')+'</div></div>' """

c = c[:idx] + new_display + c[end_idx:]
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')
