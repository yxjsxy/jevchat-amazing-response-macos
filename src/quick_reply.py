"""Click-triggered companion; the timer only inspects window metadata, never pixels."""
import objc
import AppKit as A
from Foundation import NSObject,NSMakeRect,NSTimer
import amazing

class QuickReplyWindow(NSObject):
 def initWithOwner_(self,owner):
  self=objc.super(QuickReplyWindow,self).init()
  if self is None:return None
  self.owner=owner;self.enabled=True;self.force_visible=True;self.edits=[];self.height=189;self.active_job=False;self.pinned=False;self.target_wid=None;self.main_hidden_by_wechat=False;self.hidden_by_wechat=False
  style=A.NSWindowStyleMaskTitled|A.NSWindowStyleMaskClosable|A.NSWindowStyleMaskNonactivatingPanel
  self.panel=A.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(NSMakeRect(80,220,340,self.height),style,A.NSBackingStoreBuffered,False)
  self.panel.setAppearance_(A.NSAppearance.appearanceNamed_(A.NSAppearanceNameAqua))
  self.panel.setTitle_('神回复侧边助手');self.panel.setReleasedWhenClosed_(False);self.panel.setDelegate_(self);self.panel.setLevel_(A.NSFloatingWindowLevel);self.panel.setHidesOnDeactivate_(False);self.panel.setBecomesKeyOnlyIfNeeded_(True)
  self.panel.setBackgroundColor_(A.NSColor.colorWithCalibratedRed_green_blue_alpha_(.965,.952,.99,1));self.root=self.panel.contentView()
  self.button=owner._button(self.root,'识别当前聊天并生成','start:',12,140,316,34,True);self.button.setTarget_(self)
  self.tone=A.NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(12,101,133,30),False);self.tone.addItemsWithTitles_(list(amazing.TONES));self.root.addSubview_(self.tone)
  self.level=A.NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(151,101,116,30),False);self.level.addItemsWithTitles_(list(amazing.STRENGTHS));self.level.selectItemAtIndex_(amazing.strength());self.root.addSubview_(self.level)
  self.more=owner._button(self.root,'设置','settings:',272,101,56,30);self.more.setTarget_(self)
  self.cancel=owner._button(self.root,'取消','cancel:',12,62,60,28);self.cancel.setTarget_(self);self.cancel.setEnabled_(False)
  self.status=owner._label(self.root,'仅点击时读取并生成，不自动发送。',78,59,250,36,11,owner.muted)
  self.context=owner._label(self.root,'识别后显示本轮会话和回复对象。',12,10,316,42,12,owner.ink)
  self.scroll=A.NSScrollView.alloc().initWithFrame_(NSMakeRect(10,10,320,0));self.scroll.setHasVerticalScroller_(True);self.scroll.setDrawsBackground_(False)
  self.output=A.NSView.alloc().initWithFrame_(NSMakeRect(0,0,300,0));self.scroll.setDocumentView_(self.output);self.root.addSubview_(self.scroll)
  self.timer=NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(.5,self,'tick:',None,True)
  self.panel.orderFrontRegardless();return self
 @objc.python_method
 def show(self):self.enabled=True;self.force_visible=True;self.panel.orderFrontRegardless()
 def windowWillClose_(self,notification):
  self.enabled=False;self.pinned=False
  if self.active_job and self.owner.busy:self.owner.cancel_(None)
 def start_(self,sender):
  if not self.owner._available():self.status.setStringValue_('上一任务仍在收尾，请稍后再点。');return
  self.owner.tone.selectItemWithTitle_(self.tone.titleOfSelectedItem());self.owner.level.setSelectedSegment_(int(self.level.indexOfSelectedItem()))
  self.owner._quick_requested=True;self.active_job=True;self.pinned=True;self.owner._capture(True)
 def cancel_(self,sender):self.owner.cancel_(None)
 def settings_(self,sender):
  for a,b in zip(self.edits,self.owner.edits):b.setString_(a.string())
  self.pinned=False;self.panel.orderOut_(None);self.owner.show()
 def copy_(self,sender):
  i=int(sender.tag());text=str(self.edits[i].string());pb=A.NSPasteboard.generalPasteboard();pb.clearContents();pb.setString_forType_(text,A.NSPasteboardTypeString)
  if i<len(self.owner.edits):self.owner.edits[i].setString_(text)
  self.status.setStringValue_('已复制；回微信自行粘贴、发送。');self.owner.status.setStringValue_('已复制；回微信自行粘贴、发送。')
 @objc.python_method
 def render(self,candidates):
  for v in list(self.output.subviews()):v.removeFromSuperview()
  content_h=130*len(candidates);self.height=min(640,189+content_h);self.output.setFrameSize_((300,content_h));self.edits=[]
  for i,c in enumerate(candidates):
   y=content_h-(i+1)*130
   edit=self.owner._textview(self.output,3,y+39,292,86,15);edit.setString_(c['text']);self.edits.append(edit)
   b=self.owner._button(self.output,'复制这句','copy:',4,y+4,110,29);b.setTarget_(self);b.setTag_(i)
  self._layout();self.output.scrollPoint_((0,max(0,content_h-(self.height-189))))
 @objc.python_method
 def _layout(self):
  top=self.panel.frame().origin.y+self.panel.frame().size.height
  self.panel.setContentSize_((340,self.height))
  self.panel.setFrameOrigin_((self.panel.frame().origin.x,top-self.panel.frame().size.height))
  extra=self.height-189
  for v,rect in [(self.button,(12,140+extra,316,34)),(self.tone,(12,101+extra,133,30)),(self.level,(151,101+extra,116,30)),(self.more,(272,101+extra,56,30)),(self.cancel,(12,62+extra,60,28)),(self.status,(78,59+extra,250,36)),(self.context,(12,10+extra,316,42)),(self.scroll,(10,10,320,extra))]:v.setFrame_(NSMakeRect(*rect))
 def tick_(self,timer):
  busy=self.owner.busy
  self.button.setEnabled_(not busy);self.tone.setEnabled_(not busy);self.level.setEnabled_(not busy);self.cancel.setEnabled_(busy)
  if self.active_job:self.status.setStringValue_(str(self.owner.status.stringValue()))
  if not self.enabled:return
  from apps.registry import frontmost_app,UNKNOWN
  app=frontmost_app()
  if app is UNKNOWN:return
  from perception import find_wechat_window,window_is_onscreen
  win=None
  if self.target_wid is None or (app is not None and app.key=='wechat'):
   win=find_wechat_window(previous_wid=self.target_wid)
   if win:self.target_wid=win.wid
  # Minimize changes the foreground app, so check this before the focus branches.
  # Hide only the panel; retain edits, completed results and any running job.
  if self.target_wid is not None and window_is_onscreen(self.target_wid) is False:
   if not self.hidden_by_wechat:print('[amazing-companion] hidden: WeChat target minimized/offscreen; drafts retained',flush=True)
   self.hidden_by_wechat=True
   if self.owner.window.isVisible():
    self.main_hidden_by_wechat=True;self.owner.window.orderOut_(None)
   self.panel.orderOut_(None);return
  if self.hidden_by_wechat:
   self.hidden_by_wechat=False;print('[amazing-companion] restored: WeChat target onscreen; drafts retained',flush=True)
  if self.main_hidden_by_wechat:
   self.main_hidden_by_wechat=False;self.owner.window.orderFrontRegardless()
  if app is not None and app.key=='wechat':
   self.force_visible=False
   if win:
    screen=A.NSScreen.mainScreen().visibleFrame();full=A.NSScreen.mainScreen().frame();x=win.x+win.w+8
    if x+340>screen.origin.x+screen.size.width:x=win.x-348
    x=max(screen.origin.x,min(x,screen.origin.x+screen.size.width-340));y=full.origin.y+full.size.height-win.y-self.panel.frame().size.height-70
    y=max(screen.origin.y,min(y,screen.origin.y+screen.size.height-self.panel.frame().size.height))
    self.panel.setFrameOrigin_((x,y))
   self.panel.orderFrontRegardless()
  elif not self.force_visible and not busy and not self.pinned:
   front=A.NSWorkspace.sharedWorkspace().frontmostApplication()
   if front is not None and front.bundleIdentifier()!='local.jev.amazing.response':self.panel.orderOut_(None)
