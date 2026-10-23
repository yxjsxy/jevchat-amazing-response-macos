import unittest,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import amazing
class FakeTransport:
    def __init__(self, answers):self.answers=iter(answers);self.calls=[]
    def _call(self,prompt):self.calls.append(prompt);return next(self.answers)
class AmazingTests(unittest.TestCase):
    def test_parser_preserves_speakers_and_multiline(self):
        self.assertEqual(amazing.parse_conversation("我：加班\n对方:又加班？\n第二行"),[("me","加班"),("other","又加班？\n第二行")])
    def test_latest_ten_without_per_message_truncation(self):
        long="长消息"*10000
        data=amazing.parse_conversation("\n".join("对方："+str(i)for i in range(11))+"\n对方："+long)
        self.assertEqual(len(data),10);self.assertEqual(data[-1][1],long)
    def test_all_five_styles_are_distinct(self):
        self.assertEqual(len({amazing.prompt("你怎么才回",tone,"熟悉朋友",3,1)for tone in amazing.TONES}),5)
    def test_english_and_avoid_reach_actual_prompt(self):
        p=amazing.prompt("Why are you late?","接梗","friends",3,2,["Previously shown"])
        self.assertIn("不夹中文",p);self.assertIn("放开点",p);self.assertIn("Previously shown",p)
    def test_invalid_candidates_are_rewritten_once_using_real_transport_interface(self):
        f=FakeTransport([json.dumps(["你管得着吗"],ensure_ascii=False),json.dumps(["开机慢了点"],ensure_ascii=False)])
        texts,error=amazing.generate_tone(f,"你怎么才回","自嘲","熟悉朋友",1)
        self.assertFalse(error);self.assertEqual(texts,["开机慢了点"]);self.assertEqual(len(f.calls),2)
    def test_no_padding_and_no_third_retry(self):
        f=FakeTransport(['["相同","相同"]','not JSON'])
        texts,error=amazing.generate_tone(f,"你怎么才回","自然","",2)
        self.assertEqual(texts,[]);self.assertTrue(error);self.assertEqual(len(f.calls),2)
    def test_observed_personal_attack_is_rejected(self):
        self.assertTrue(amazing.issues(["再睡会就能追上你的发际线了"],1,"你怎么这么能睡"))
    def test_english_does_not_accept_chinese_candidates(self):
        self.assertTrue(amazing.issues(["Sorry，刚看到"],1,"Why are you late?"))
        self.assertFalse(amazing.issues(["My phone hit snooze."],1,"Why are you late?"))
    def test_rank_instruction_does_not_claim_objective_humor(self):
        self.assertIn("not objective humor scores",amazing.ranking_instructions())


class AutomaticChatTitleTests(__import__('unittest').TestCase):
 def test_uses_actual_header_without_typed_name(self):
  from types import SimpleNamespace as M
  title,raw,n=amazing.captured_chat({'ok':True,'chat_title':'  当前聊天  ','messages':[M(side='me',text='早'),M(side='unknown',text='不是可确认正文'),M(side='them',text='早上好')]})
  self.assertEqual((title,raw,n),('当前聊天','我：早\n对方：早上好',2))
 def test_does_not_guess_missing_header(self):
  from types import SimpleNamespace as M
  with self.assertRaisesRegex(ValueError,'标题'):
   amazing.captured_chat({'ok':True,'chat_title':'','messages':[M(side='them',text='可能是联系人名')]})
 def test_reports_capture_error(self):
  with self.assertRaisesRegex(ValueError,'读取失败'):
   amazing.captured_chat({'ok':False,'error':'capture failed'})


class ClickCaptureRetryTests(unittest.TestCase):
 def test_does_not_recapture_readable_frame(self):
  from types import SimpleNamespace as M
  from unittest.mock import Mock
  read=Mock(return_value={'ok':True,'chat_title':'当前会话','messages':[M(side='them',text='早上好')]})
  self.assertEqual(amazing.capture_current(read)[1],'对方：早上好')
  self.assertEqual(read.call_count,1)
 def test_retries_once_on_same_window(self):
  from types import SimpleNamespace as M
  from unittest.mock import Mock,patch
  read=Mock(side_effect=[{'ok':True,'chat_title':'当前会话','messages':[],'window':{'wid':42}}, {'ok':True,'chat_title':'当前会话','messages':[M(side='them',text='早上好')]}])
  with patch('amazing.time.sleep'):self.assertEqual(amazing.capture_current(read)[2],1)
  self.assertEqual(read.call_count,2);read.assert_called_with(previous_wid=42)
 def test_never_loops_after_second_failure(self):
  from unittest.mock import Mock,patch
  read=Mock(return_value={'ok':False,'error':'capture failed'})
  with patch('amazing.time.sleep'),self.assertRaises(ValueError):amazing.capture_current(read)
  self.assertEqual(read.call_count,2)
