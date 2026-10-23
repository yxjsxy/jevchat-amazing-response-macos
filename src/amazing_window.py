"""Native, user-operated playground inside the official macOS client fork."""
from __future__ import annotations
import objc,threading,time,uuid,json
from pathlib import Path
import AppKit as A
from Foundation import NSObject,NSMakeRect,NSTimer
import amazing,userconfig
from generate import Generator
from judge_jev import JevJudge
from settings_config import error_message

class AmazingWindow(NSObject):
 def initWithHud_(self,hud):
  self=objc.super(AmazingWindow,self).init()
  if self is None:return None
  self.hud=hud;self.epoch=0;self.busy=False;self.worker=None;self.last=None;self.edits=[];self.phase='';self.started=0;self.job='';self.snapshot=None
  self.accent=A.NSColor.colorWithCalibratedRed_green_blue_alpha_(.39,.25,.82,1)
  self.ink=A.NSColor.colorWithCalibratedWhite_alpha_(.13,1);self.muted=A.NSColor.colorWithCalibratedWhite_alpha_(.46,1)
  self.window=A.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(NSMakeRect(0,0,980,724),A.NSWindowStyleMaskTitled|A.NSWindowStyleMaskClosable|A.NSWindowStyleMaskMiniaturizable,A.NSBackingStoreBuffered,False)
  self.window.setAppearance_(A.NSAppearance.appearanceNamed_(A.NSAppearanceNameAqua))
  self.window.setDelegate_(self)
  self.window.setTitle_('神回复 · 基于 Jev macOS 的本地修改版');self.window.setReleasedWhenClosed_(False);self.window.center()
  self.window.setBackgroundColor_(A.NSColor.colorWithCalibratedRed_green_blue_alpha_(.965,.952,.99,1))
  root=self.window.contentView();self.root=root
  self._label(root,'JEV / AMAZING RESPONSE',26,680,700,20,11,self.accent)
  self._label(root,'接住这一句。',26,628,600,46,32,self.ink,True)
  self.replyInfo=self._label(root,'点击时理解当前聊天文字、图片与表情包；先确认回复对象。',27,597,650,32,12,self.muted)
  self.read=self._button(root,'打开侧边助手','readScreen:',686,648,144,32)
  self.target=A.NSTextField.labelWithString_('会话：读取后自动识别');self.target.setFrame_(NSMakeRect(686,613,262,28));root.addSubview_(self.target)
  self.settings=self._button(root,'接口设置','settings:',836,648,112,32)
  self._label(root,'01  最近聊到哪了',26,571,440,24,15,self.ink,True)
  self.conversation=self._textview(root,26,330,440,234,15)
  self.conversation.setString_('我：今天加班到九点\n对方：公司离了你是不是得倒闭？')
  self._label(root,'用 我：/ 对方：分行；只发送最近10条。支持直接粘贴和编辑。',27,302,440,22,11,self.muted)
  self.paste=self._button(root,'粘贴文字','pasteInput:',26,263,105,30)
  self.image=self._button(root,'识别截图…','importImage:',139,263,113,30)
  self.capture=self._button(root,'识别并生成','captureChat:',260,263,160,30)
  self._label(root,'02  你们是什么关系',26,221,440,23,15,self.ink,True)
  self.relationship=A.NSTextField.alloc().initWithFrame_(NSMakeRect(26,180,440,34));self.relationship.setPlaceholderString_('例如：熟悉的朋友，平时会互相开玩笑');self.relationship.setStringValue_('熟悉的朋友，平时会互相开玩笑');root.addSubview_(self.relationship)
  self._label(root,'03  想怎么接',26,144,440,22,15,self.ink,True)
  self.tone=A.NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(26,104,125,31),False);self.tone.addItemsWithTitles_(list(amazing.TONES));root.addSubview_(self.tone)
  self.level=A.NSSegmentedControl.alloc().initWithFrame_(NSMakeRect(158,106,308,28));self.level.setSegmentCount_(3)
  for i,text in enumerate(amazing.STRENGTHS):self.level.setLabel_forSegment_(text,i);self.level.setWidth_forSegment_(100,i)
  self.level.setSelectedSegment_(amazing.strength());self.level.setTarget_(self);self.level.setAction_('strengthChanged:');root.addSubview_(self.level)
  self.generate=self._button(root,'生成神回复','start:',26,51,144,36,True)
  self.again=self._button(root,'再来一组','again:',180,51,130,36)
  self.cancel=self._button(root,'取消','cancel:',320,51,70,36)
  self.count=A.NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(397,53,69,31),False);self.count.addItemsWithTitles_(['1条','2条','3条','4条','5条']);self.count.selectItemAtIndex_(2);root.addSubview_(self.count)
  self._label(root,'候选草稿',496,571,300,24,15,self.ink,True)
  self._label(root,'可以直接修改；排序仅供参考。',496,548,450,22,12,self.muted)
  self.outputScroll=A.NSScrollView.alloc().initWithFrame_(NSMakeRect(496,91,454,450));self.outputScroll.setHasVerticalScroller_(True);self.outputScroll.setDrawsBackground_(False)
  self.output=A.NSView.alloc().initWithFrame_(NSMakeRect(0,0,436,450));self.outputScroll.setDocumentView_(self.output);root.addSubview_(self.outputScroll)
  self.empty=self._label(self.output,'这里会出现真实模型生成的候选。\n\n没有预制答案，也不会自动发送。',22,298,400,110,17,self.muted)
  self.save=self._button(root,'保存本轮草稿…','save:',496,51,180,34);self.save.setEnabled_(False)
  self.status=self._label(root,'已就绪 · 云接口会使用你自己的API额度；截图OCR在本机完成。',26,9,924,32,11,self.muted)
  self.timer=NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(.5,self,'tick:',None,True)
  self._set_busy(False)
  return self

 @objc.python_method
 def _label(self,parent,text,x,y,w,h,size=13,color=None,bold=False):
  v=A.NSTextField.labelWithString_(text);v.setFrame_(NSMakeRect(x,y,w,h));v.setFont_(A.NSFont.boldSystemFontOfSize_(size)if bold else A.NSFont.systemFontOfSize_(size));v.setTextColor_(color or self.ink);v.setMaximumNumberOfLines_(0);v.setLineBreakMode_(A.NSLineBreakByWordWrapping);parent.addSubview_(v);return v
 @objc.python_method
 def _button(self,parent,text,action,x,y,w,h,primary=False):
  v=A.NSButton.alloc().initWithFrame_(NSMakeRect(x,y,w,h));v.setTitle_(text);v.setBezelStyle_(A.NSBezelStyleRounded);v.setTarget_(self);v.setAction_(action)
  if primary:v.setBezelColor_(self.accent)
  parent.addSubview_(v);return v
 @objc.python_method
 def _textview(self,parent,x,y,w,h,size=15):
  scroll=A.NSScrollView.alloc().initWithFrame_(NSMakeRect(x,y,w,h));scroll.setHasVerticalScroller_(True);scroll.setBorderType_(A.NSBezelBorder)
  v=A.NSTextView.alloc().initWithFrame_(NSMakeRect(0,0,w-20,h));v.setRichText_(False);v.setFont_(A.NSFont.systemFontOfSize_(size));v.setTextColor_(self.ink);v.setBackgroundColor_(A.NSColor.whiteColor());v.setTextContainerInset_((10,10));v.setVerticallyResizable_(True);v.setHorizontallyResizable_(False);v.textContainer().setWidthTracksTextView_(True);scroll.setDocumentView_(v);parent.addSubview_(scroll);return v
 @objc.python_method
 def show(self):
  self.window.makeKeyAndOrderFront_(None);A.NSApp.activateIgnoringOtherApps_(True)
 @objc.python_method
 def _set_busy(self,value):
  self.busy=value
  for v in [self.read,self.generate,self.paste,self.image,self.capture,self.tone,self.level,self.count,self.settings]:v.setEnabled_(not value)
  self.conversation.setEditable_(not value);self.relationship.setEnabled_(not value);self.again.setEnabled_(not value and self.last is not None);self.cancel.setEnabled_(value);self.save.setEnabled_(not value and bool(self.edits))
 @objc.python_method
 def _available(self):
  if self.busy:return False
  if self.worker and self.worker.is_alive():self.status.setStringValue_('上次云请求仍在收尾，完成后即可再试；取消不能保证云端停止计费。');return False
  return True
 def windowWillClose_(self,notification):
  if self.busy:self.cancel_(None)
 def readScreen_(self,sender):
  self.quick.show();self.window.orderOut_(None)
 def settings_(self,sender):self.hud.openSettings_(sender)
 def strengthChanged_(self,sender):
  self.hud.set_amazing_strength(int(self.level.selectedSegment()))
 def pasteInput_(self,sender):
  text=A.NSPasteboard.generalPasteboard().stringForType_(A.NSPasteboardTypeString)
  if text:self.conversation.setString_(text)
  else:self.status.setStringValue_('剪贴板里没有文字；可以手动输入，或选择截图文件。')
 def start_(self,sender):self._start(False)
 def again_(self,sender):self._start(True)
 @objc.python_method
 def _start(self,again,after_capture=False):
  if not after_capture and not self._available():return
  raw=str(self.conversation.string()).strip();messages=amazing.parse_conversation(raw)
  if not messages:self.status.setStringValue_('请先输入自己的对话。');return
  if messages[-1][0]=='me':self.status.setStringValue_('最后一条请标为对方，才能生成接话。');return
  relation=str(self.relationship.stringValue()).strip()or'普通朋友，尚不熟悉';tone=str(self.tone.titleOfSelectedItem());level=int(self.level.selectedSegment());count=int(self.count.indexOfSelectedItem())+1
  signature=(raw,relation,tone,level,count);avoid=self.last['original_candidates']if again and self.last and self.last['signature']==signature else []
  self.epoch+=1;run=self.epoch
  if not after_capture:self.job=uuid.uuid4().hex[:8];self.started=time.monotonic()
  source=self.snapshot if self.snapshot and self.snapshot.raw==raw else None
  source_label=source.label if source else '手动输入 · 回复最后一条对方消息'
  self.replyInfo.setStringValue_(source_label)
  self.phase=f'正在生成{count}条神回复';self._set_busy(True)
  context='关系：'+relation+'\n最近对话：\n'+'\n'.join(('我：'if side=='me'else'对方：')+text for side,text in messages)
  if source:context+='\n回复对象已对照当前点击画面：'+source.target_id+' / '+source.target_kind+'。针对最后这条整体接话，图片描述是可见内容，视觉含义推测不等于事实，不编造动画或未展示内容。'
  def work():
   try:
    texts,error=amazing.generate_tone(Generator(timeout=25),messages[-1][1],tone,context,count,level=level,avoid=avoid)
    if error:raise ValueError(error)
    if run!=self.epoch:return
    self._post({'run':run,'stage':'正在比较候选'})
    if count>1:
     judge=JevJudge(timeout=25)
     ranked=judge.rank_candidates(messages[-1][1],'神回复',texts,context=context+'\n本轮风格：'+tone+'；力度：'+amazing.STRENGTHS[level])
    else:ranked=[{'text':texts[0],'prob':1.0}]
    self._post({'run':run,'result':ranked,'metadata':{'signature':signature,'raw':raw,'relationship':relation,'tone':tone,'strength':amazing.STRENGTHS[level],'original_candidates':texts,'job':self.job,'source_label':source_label,'visual_model':source.model if source else None,'target_kind':source.target_kind if source else 'text'},'seconds':time.monotonic()-self.started})
   except Exception as exc:
    message=str(exc)if isinstance(exc,ValueError)else error_message(exc)
    for key in [userconfig.get('OPENAI_API_KEY'),userconfig.get('TYPESAFE_API_KEY'),userconfig.get('JEV_VISION_API_KEY')]:
     if key:message=message.replace(key,'[已隐藏]')
    self._post({'run':run,'error':message[:240]})
  self.worker=threading.Thread(target=work,daemon=True);self.worker.start()
 @objc.python_method
 def _post(self,payload):self.performSelectorOnMainThread_withObject_waitUntilDone_('receive:',payload,False)
 def receive_(self,payload):
  if int(payload['run'])!=self.epoch:return
  if 'stage'in payload:self.phase=payload['stage'];return
  self._set_busy(False)
  if 'error'in payload:
   self.status.setStringValue_('本轮未完成：'+payload['error']+'。已有草稿仍保留。')
   self.replyInfo.setStringValue_('本轮读取/校验未完成；下方旧草稿不代表当前聊天。')
   if getattr(self,'_quick_requested',False):self.quick.context.setStringValue_('本轮未完成；下方保留上轮草稿，请勿当作当前回复。')
   return
  if 'chat'in payload:
   self.snapshot=payload.get('snapshot')
   if self.snapshot:
    self.replyInfo.setStringValue_(self.snapshot.label)
    if getattr(self,'_quick_requested',False):self.quick.context.setStringValue_(self.snapshot.label)
   self.target.setStringValue_('会话：'+payload['chat_title'])
   self.conversation.setString_(payload['chat'])
   self.status.setStringValue_(f"已识别当前会话 · {payload['n_messages']}条 · {payload['seconds']:.1f}秒")
   if payload.get('generate'):self._start(False,after_capture=True)
   return
  if 'ocr'in payload:
   self.conversation.setString_(payload['ocr']);self.status.setStringValue_('已在本机识别截图。说话人和顺序尚未确认，请编辑成 我：/ 对方：后生成。');return
  self.last=dict(payload['metadata']);self._render(list(payload['result']));self._set_busy(False)
  if getattr(self,'_quick_requested',False):
   self.quick.context.setStringValue_(self.last.get('source_label',''))
   self.quick.render(list(payload['result']))
  self.status.setStringValue_(f"本轮 {self.last['job']} · {float(payload['seconds']):.1f}秒 · {len(self.edits)}条真实候选。修改后再复制。")
 @objc.python_method
 def _render(self,candidates):
  for v in list(self.output.subviews()):v.removeFromSuperview()
  height=max(450,len(candidates)*166+12);self.output.setFrameSize_((436,height));self.edits=[]
  for i,item in enumerate(candidates):
   y=height-(i+1)*166
   self._label(self.output,f"0{i+1} / {self.last['tone']}",16,y+137,395,20,11,self.accent,True)
   edit=self._textview(self.output,16,y+47,400,86,18);edit.setString_(item['text']);self.edits.append(edit)
   button=self._button(self.output,'复制这句','copyCandidate:',16,y+9,118,30);button.setTag_(i)
  self.output.scrollPoint_((0,max(0,height-450)))
 def copyCandidate_(self,sender):
  i=int(sender.tag());text=str(self.edits[i].string());pb=A.NSPasteboard.generalPasteboard();pb.clearContents();pb.setString_forType_(text,A.NSPasteboardTypeString);self.status.setStringValue_('已复制你编辑后的文字。回聊天窗口自行粘贴、发送。')
 def cancel_(self,sender):
  self.epoch+=1;self._set_busy(False);self.status.setStringValue_('已取消接收本轮结果；已发出的云请求仍可能完成和计费。')
 def tick_(self,timer):
  if self.busy:
   elapsed=time.monotonic()-self.started
   if elapsed>90:self.cancel_(None);self.status.setStringValue_('本轮达到90秒保护上限，已停止接收结果；稍后可重试。')
   else:self.status.setStringValue_(f'{self.phase} · {elapsed:.0f}秒 · {self.job}')
 def save_(self,sender):
  if not self.last:return
  panel=A.NSSavePanel.savePanel();panel.setNameFieldStringValue_('神回复-'+self.last['job']+'.txt')
  if panel.runModal()==A.NSModalResponseOK:
   text='神回复 / '+self.last['job']+'\n风格：'+self.last['tone']+' / '+self.last['strength']+'\n关系：'+self.last['relationship']+'\n\n输入：\n'+self.last['raw']+'\n\n草稿（含你的修改）：\n'+'\n\n'.join(f'{i+1}. {v.string()}'for i,v in enumerate(self.edits))
   try:Path(str(panel.URL().path())).write_text(text,encoding='utf-8');self.status.setStringValue_('草稿已保存到你选择的位置。')
   except OSError:self.status.setStringValue_('所选位置无法写入，请换目录，或复制单条草稿。')
 def captureChat_(self,sender):
  self._quick_requested=False;self._capture(True)
 @objc.python_method
 def _capture(self,auto_generate):
  if not self._available():return
  # CGPreflight may be stale after a grant; let macOS enforce the actual capture.
  if not self.hud._paused:self.hud.togglePause_(None)
  self.epoch+=1;run=self.epoch;self.job=uuid.uuid4().hex[:8];self.started=time.monotonic();self.phase='正在读取当前窗口文字与图片';self._set_busy(True)
  if getattr(self,'_quick_requested',False):self.quick.context.setStringValue_('正在读取新窗口；下方旧候选尚未更新。')
  def work():
   try:
    from visual_chat import capture_current
    result=capture_current(stage=lambda text:self._post({'run':run,'stage':text}),cancelled=lambda:run!=self.epoch)
    self._post({'run':run,'chat':result.raw,'chat_title':result.title,'snapshot':result,'generate':auto_generate,'n_messages':len(result.messages),'seconds':time.monotonic()-self.started})
   except Exception as exc:self._post({'run':run,'error':str(exc)if isinstance(exc,ValueError)else'微信读取失败：'+type(exc).__name__})
  self.worker=threading.Thread(target=work,daemon=True);self.worker.start()
 def importImage_(self,sender):
  if not self._available():return
  panel=A.NSOpenPanel.openPanel();panel.setCanChooseDirectories_(False);panel.setAllowsMultipleSelection_(False);panel.setAllowedFileTypes_(['png','jpg','jpeg','tiff','heic'])
  if panel.runModal()!=A.NSModalResponseOK:return
  path=Path(str(panel.URL().path()));self.epoch+=1;run=self.epoch;self.job=uuid.uuid4().hex[:8];self.started=time.monotonic();self.phase='正在本机识别截图';self._set_busy(True)
  def work():
   try:
    from perception import _load_png_image,ocr_image
    image=_load_png_image(path)
    if image is None:raise ValueError('无法读取图片，请选择有效截图')
    blocks=ocr_image(image,chat_only=False)
    text='\n'.join(b.text for b in sorted(blocks,key=lambda b:(-b.y,b.x)))
    if not text.strip():raise ValueError('截图里没有识别到可读文字')
    self._post({'run':run,'ocr':text})
   except Exception as exc:self._post({'run':run,'error':str(exc)if isinstance(exc,ValueError)else'截图识别失败，请更换清晰图片'})
  self.worker=threading.Thread(target=work,daemon=True);self.worker.start()
