print("Startup...")
# init
# using SendGrid, Pygame, nfcpy, requests (required pip install)
# https://sendgrid.kke.co.jp/docs/Integrate/Code_Examples/v3_Mail/python.html
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import tkinter as tk
from datetime import datetime as dt
from datetime import timedelta as td
import nfc
from threading import Thread as th
from time import sleep
from pygame import mixer as mx
from csv import reader as rdr
from csv import writer as wtr
from os import path as pt
from os import environ as ev
from collections import deque
from requests import get as rg
import xml.etree.ElementTree as et

# if you need, write proxy address here
ev["http_proxy"] = ""
ev["https_proxy"] = ""

tx_title="電算研_図書管理"
tx_ver="v1.0"

gray="#444444"
white="#ffffff"
great="#008a00"
info="#0070f0"
warn="#807500"
ftal="#cc0000"

# max,ctdn,day
CONFIG=[4,20,7]

# flag [main,serv]
FLAG=[True,False]
RPTNUM=[0,0]
# dict_lib,usr_lib
EXT=[dict(),dict()]
USD=[dict(),dict()]; PBD=[dict(),False]
CNTDN=[False,0,0]
# ReadOK,SID,Mail,Perm
STID=[False,"",-1,0]
ISBN=[""]
MAIL_Q = deque()
C_DATE = dt.today().date()

# == Card reader ==
class mCardReader(object):
    global FLAG
    def on_connect(self, tag):
        #touched
        stat_update(info,"読み込み中...",
                    "学生証を動かさないでください...","\uf16a")
        # Load Student No. from IC CARD
        try:
            id= tag.identifier
            FLAG[1] = (id == b"\x12\xb6h\x1b")
            tag.polling(system_code=0x93B1)
            sc = nfc.tag.tt3.ServiceCode(64, 0x0b)
            bc = nfc.tag.tt3.BlockCode(0, service=0)
            data = tag.read_without_encryption([sc], [bc])

            STID[1] = data.decode('utf-8').lstrip('0').rstrip()[:-2]
            
            if STID[1] in EXT[1]:
                stat_update(great,"{} さん こんにちは".format(EXT[1][STID[1]]),
                            "学生証を離すと次へ進みます","\ue10b")
                mplay("snd/great.mp3")
                STID[0] = True
            else:
                stat_update(ftal,"[E13] {} さん 未登録者です".format(STID[1]),
                            "ご利用いただけません","\uee57")
                mplay("snd/forb.mp3")
        except AttributeError:
            if not(FLAG[1]):
                mplay("snd/error3.mp3")
                stat_update(warn,"[E10] KIT学生証ではありません",
                            "カードを離してください","\ue1e0")
            mplay("snd/special.mp3")
        except nfc.tag.tt3.Type3TagCommandError:
            mplay("snd/retry.mp3")
            stat_update(warn,"[E11] もう一度やり直してください",
                        "カードを離してください","\uea6a")
        return True

    def read_id(self):
        try:
            stat_update(info,"KIT学生証をかざしてください",
                        "返却日は {} です".format((dt.today()+td(days=CONFIG[2])).strftime("%Y/%m/%d") ),"\ued5c")
            clf = nfc.ContactlessFrontend('usb')
            try:
                clf.connect(rdwr={'on-connect': self.on_connect})
            finally:
                clf.close()
        except Exception as e:
            print("C.Err:",e)
            mplay("snd/crit.mp3")
            for i in range(4,-1,-1):
                stat_update(ftal,"[E01] カードリーダー未接続 ({})".format(i),
                            "接続を確認してください","\ueb55")
                slp(1)
        slp(.3)
# =================

#tkinter init
root = tk.Tk()
#title setting
root.title((tx_title,tx_ver))
#window size setting
root.attributes("-fullscreen",True)
#sound setting
mx.init(frequency= 44100)

def slp(time):
	sleep(time if FLAG[0] else 0)

def mplay(addr):
    mx.music.load(addr)
    mx.music.play()
		 
def dictSYS():
    global USD
    while FLAG[0]:
        STID[0]=False; STID[1]=""; STID[2]=-1; STID[3]=0
        stat_update(info,"カードリーダ準備中...",
                    "お待ちください","\uf16a")
        upld_update("Ready")
        mCardReader().read_id()
        if FLAG[1]:
            CNTDN[0] = True; CNTDN[1] = 60; CNTDN[2] = 0
            isbnS.focus_set()
            isbnS.config(state=tk.NORMAL)
            isbnS.bind('<Return>', service)
            stat_update(gray,"サービスモード",
                        "操作待機中","\ue115")
            while CNTDN[0]:
                slp(.3)
            isbnS.config(state=tk.DISABLED)
            isbnS.unbind('<Return>')
            FLAG[1]=False
            continue
        if not(STID[0]): continue

        try:
            USD[0]=dict()
            if pt.isfile("usr/"+STID[1]+".csv"):
                with open("usr/"+STID[1]+".csv") as f:
                    tmp=next(f).strip("\n").split(",")
                    STID[2]=int(tmp[0]); STID[3]=int(tmp[1])
                    for row in rdr(f):
                        USD[0] = {**USD[0],row[0]:row[1]}
        except Exception as e:
            ex="U.Err: "+str(e)
            print(ex+"\n")
            stat_update(ftal,"[E15] ユーザーデータが破損しています",
                        "管理者に連絡してください","\uee57")
            mplay("snd/crit.mp3")
            slp(3)
            continue

        USD[1]=dict()
        for i in zip(USD[0].keys(), USD[0].values()):
            tmpa = dt.today()
            tmpb = dt.strptime(i[1],"%Y-%m-%d")
            if dt.date(tmpa) > dt.date(tmpb):
                stat_update(warn,"貸出期限が過ぎています",
                            "{}".format(EXT[0][i[0]]),"\ue163")
                mplay("snd/special.mp3")
                USD[1] = {**USD[1],i[0]:i[1]}
                slp(5)

        CNTDN[0] = True; CNTDN[1] = CONFIG[1]; CNTDN[2] = 0
        isbnS.focus_set()
        isbnS.config(state=tk.NORMAL)

        if len(USD[1]):
            isbnS.bind('<Return>', retnONLY)
            stat_update(warn,"貸出期限が過ぎた書籍を返却してください",
                        "書籍裏面にある 上段 のバーコードを読み込ませます","\uee6f\uec5a")
            while CNTDN[0]:
                upld_update("User: {} - Stat. {}/{}".format(STID[1],STID[3],CONFIG[0]))
                if CNTDN[1]==10: 
                    stat_update(warn,"貸出期限が過ぎた書籍を返却してください",
                                "終了コードを読み込むと返却を中断します","\uee6f\uec5a")
                slp(.3)
            if PBD[1] : mailPST(2,STID[1],STID[2],EXT[1][STID[1]],USD[0].copy())
        elif STID[2]!=-1:
            isbnS.bind('<Return>', dictUPD)
            stat_update(info,"ISBNをスキャンしてください",
                        "書籍裏面にある 上段 のバーコードを読み込ませます","\uee6f\uec5a")
            while CNTDN[0]:
                upld_update("User: {} - Stat. {}/{}".format(STID[1],STID[3],CONFIG[0]))
                if CNTDN[1]==10: 
                    stat_update(info,"ISBNをスキャンしてください",
                                "終了コードを読み込むとログアウトします","\uee6f\uec5a")
                slp(.3)
            if PBD[1] : mailPST(2,STID[1],STID[2],EXT[1][STID[1]],USD[0].copy())
        else:
            isbnS.bind('<Return>', mailUPD)
            stat_update(info,"ご利用のメールアドレスを設定してください",
                        "学籍番号: {} - 設定するバーコードを読み込ませます".format(STID[1]),"\ue779")   
            while CNTDN[0]:
                upld_update("New Account Setup")
                slp(.3)
            if STID[2] !=-1:
                STID[3] = CONFIG[0]
                mailPST(1,STID[1],STID[2],EXT[1][STID[1]],None)

        isbnS.config(state=tk.DISABLED)
        isbnS.unbind('<Return>')
        stat_update(info,"ログアウトしています...",
                    "ユーザーデータを保存しています","\uf16a")
        try:
            with open("usr/"+STID[1]+".csv",mode="w",encoding="cp932",newline="") as f:
                wtr(f).writerow([STID[2],STID[3]])
                wtr(f).writerows(list(zip(USD[0].keys(), USD[0].values())))
        except Exception as e:
            ex="W.Err: "+str(e)
            print(ex+"\n")
            stat_update(ftal,"[E18] ユーザーデータを保存できませんでした",
                        "管理者に連絡してください","\uee57")
            mplay("snd/crit.mp3")
            slp(5)
        USD[0].clear();USD[1].clear()
        slp(.4)

def service(event):
    CNTDN[1] = 60; CNTDN[2] = 0
    ISBN[0] = isbnS.get()
    isbnS.delete(0,tk.END); isbnS.focus_set()
    if ISBN[0] == "DATA-ENDJ":
        CNTDN[0]=False
    elif ISBN[0] == "SHUTDOWNO":
        CNTDN[0]=False
        root.quit()
    elif ISBN[0] in EXT[0]:
        if ISBN[0] in PBD[0]:
            try:
                expday = -1
                with open("usr/{}.csv".format(PBD[0][ISBN[0]]),mode="r",encoding="cp932") as f:
                    next(f)
                    for row in rdr(f):
                        if row[0] == ISBN[0]:
                            expday = row[1]
                mplay("snd/ok.mp3")
                stat_update(great,"登録済のISBN ({})".format(ISBN[0]),
                            "{} に貸出中です - 期限: {}".format(PBD[0][ISBN[0]],expday),"\uf180")
                if expday == -1 : raise Exception
            except Exception as e:
                mplay("snd/retError.mp3")
                stat_update(warn,"登録済のISBN ({})".format(ISBN[0]),
                            "{} に貸出中です - 期限を読込めませんでした".format(PBD[0][ISBN[0]]),"\uf180")
                print("S.Err: "+e)
        else:
            mplay("snd/special2.mp3")
            stat_update(info,"登録済のISBN ({})".format(ISBN[0]),
                        "貸し出しされていません","\ue82d")
    else:
        mplay("snd/question.mp3")
        stat_update(gray,"新しいISBN ({})".format(ISBN[0]),
                    "情報取得中...","\uf16a")
        isbnS.config(state=tk.DISABLED)
        isbnS.unbind('<Return>')
        slp(1)

        try:
            title = get_new_title(ISBN[0])
            stat_update(gray,"取得成功 ({})".format(title),
                    "マスタを更新しています...","\uf16a")
            with open("dict/master.csv",mode ="a", encoding="cp932",newline="") as f:
                wtr(f).writerow([ISBN,title])
                EXT[0] = {**EXT[0], ISBN[0]:title}
                RPTNUM[1]=len(EXT[0]); RPTNUM[0]=RPTNUM[1] - len(PBD[0])
            slp(1)
            mplay("snd/great.mp3")
            stat_update(great,"追加完了 ({})".format(title),
                    "マスタを更新しました","\ue10b")
        except Exception:
            mplay("snd/error2.mp3")
            stat_update(warn,"取得失敗 ({})".format(ISBN[0]),
                            "上手くいかない場合は手動でマスタを更新してください","\uf180")
            print("S.Err: "+e)
        finally:
            isbnS.focus_set()
            isbnS.config(state=tk.NORMAL)
            isbnS.bind('<Return>', service)
    
    ISBN[0]=""
    
def get_new_title(isbn):
    res = rg("https://iss.ndl.go.jp/api/sru",
             params={
                 'operation': 'searchRetrieve',
                 'query': f'isbn="{isbn}"',
                 'recordPacking': 'xml'
                })
    root = et.fromstring(res.text)
    ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
    return root.find('.//dc:title', ns).text

def mailUPD(event):
    CNTDN[1] = CONFIG[1]; CNTDN[2] = 0
    ISBN[0] = isbnS.get()
    isbnS.delete(0,tk.END); isbnS.focus_set()
    if ISBN[0] == "DATA-ENDJ":
        CNTDN[0]=False
    elif ISBN[0]=="B-PL7":
        stat_update(great,"登録しました".format(ISBN[0]),
                    "b{}@planet.kanazawa-it.ac.jp".format(STID[1]),"\uea56")
        mplay("snd/question.mp3")
        CNTDN[1]=3; STID[2]=1
        isbnS.config(state=tk.DISABLED)
        isbnS.unbind('<Return>')
    elif ISBN[0]=="C-PL8":
        stat_update(great,"登録しました".format(ISBN[0]),
                    "c{}@planet.kanazawa-it.ac.jp".format(STID[1]),"\uea56")
        mplay("snd/question.mp3")
        CNTDN[1]=3; STID[2]=2
        isbnS.config(state=tk.DISABLED)
        isbnS.unbind('<Return>')
    elif ISBN[0]=="C-STJ":
        stat_update(great,"登録しました".format(ISBN[0]),
                    "c{}@st.kanazawa-it.ac.jp".format(STID[1]),"\uea56")
        mplay("snd/question.mp3")
        CNTDN[1]=3; STID[2]=3
        isbnS.config(state=tk.DISABLED)
        isbnS.unbind('<Return>')
    else:
        stat_update(warn,"[E20] 無効なスキャン".format(ISBN[0]),
                    "メールアドレス設定バーコードを読ませてください","\ue7ba")
        mplay("snd/error3.mp3")
    
    ISBN[0]=""

def retnONLY(event):
    global USP,PBD
    ISBN[0] = isbnS.get()
    if ISBN[0] == "DATA-ENDJ":
        CNTDN[0]=False
    elif ISBN[0][:2]=="19":
        # ingore begin from "19"
        pass
    elif ISBN[0] in USD[0] or ISBN[0] in USD[1]:
        btext = EXT[0][ISBN[0]]
        del USD[0][ISBN[0]]
        if ISBN[0] in USD[1] : del USD[1][ISBN[0]]
        del PBD[0][ISBN[0]]
        PBD[1]=True
        STID[3] += 1
        with open("log/"+dt.today().strftime('%Y%m%d')+".log",mode="a",encoding="cp932",newline="") as f:
            wtr(f).writerow([dt.now().strftime('%H:%M:%S'),"Return",STID[1],ISBN[0]])
        stat_update(great,"返却しました ({})".format(ISBN[0]),
                    "書籍名: {}".format(btext),"\ue8f1\ue0a6")
        mplay("snd/special2.mp3")
    else:
        stat_update(warn,"[E32] 貸出できません ({})".format(ISBN[0]),
                    "先に 貸出期限が過ぎた 書籍 を返却してください","\ue0ab\ue10a")
        mplay("snd/forb.mp3")
    isbnS.delete(0,tk.END);ISBN[0]=""; isbnS.focus_set()
    CNTDN[1] = CONFIG[1]; CNTDN[2] = 0

def dictUPD(event):
    global USD,PBD
    try:
        ISBN[0] = isbnS.get()
        if ISBN[0] == "DATA-ENDJ":
            CNTDN[0]=False
        elif ISBN[0][:2]=="19":
            # 19 で始まる下段コードは無視
            pass
        elif ISBN[0] in USD[0]: #ログインユーザーに貸出されているか
            btext = EXT[0][ISBN[0]]
            del USD[0][ISBN[0]]
            del PBD[0][ISBN[0]]
            PBD[1]=True
            STID[3] += 1
            with open("log/"+dt.today().strftime('%Y%m%d')+".log",mode="a",encoding="cp932",newline="") as f:
                    wtr(f).writerow([dt.now().strftime('%H:%M:%S'),"Return",STID[1],ISBN[0]])
            stat_update(great,"返却しました ({})".format(ISBN[0]),
                        "書籍名: {}".format(btext),"\ue8f1\ue0a6")
            mplay("snd/return.mp3")
        else:
            if ISBN[0] in PBD[0]:
                stat_update(warn,"[E31] 貸出できません ({})".format(ISBN[0]),
                            "他の人に貸出中の本です","\uf180")
                mplay("snd/error2.mp3")
            elif STID[3] > 0: #貸出上限
                btext = EXT[0][ISBN[0]]
                USD[0] = {**USD[0], ISBN[0]:str( (dt.today()+td(days=CONFIG[2])).strftime("%Y-%m-%d"))}
                PBD[0] = {**PBD[0], ISBN[0]:STID[1]}
                PBD[1]=True
                STID[3] -= 1
                with open("log/"+dt.today().strftime('%Y%m%d')+".log",mode="a",encoding="cp932",newline="") as f:
                    wtr(f).writerow([dt.now().strftime('%H:%M:%S'),"Lending",STID[1],ISBN[0]])

                stat_update(great,"貸出しました ({})".format(ISBN[0]),
                            "書籍名: {}".format(btext),"\ue0ab\ue82d") 
                mplay("snd/ok.mp3")
            else:
                stat_update(warn,"[E30] これ以上貸出できません ({})".format(ISBN[0]),
                            "貸出した本を返却してください","\ue0ab\ue10a")
                mplay("snd/fatal.mp3")
    except Exception as e:
        print("D.Err: "+str(e))
        stat_update(warn,"[E35] 受付できません ({})".format(ISBN[0]),
                    "書籍が登録されていない または 有効なISBNではありません","\ue7ba")
        mplay("snd/retError.mp3")
    finally:
        isbnS.delete(0,tk.END);ISBN[0]=""; isbnS.focus_set()
        CNTDN[1] = CONFIG[1]; CNTDN[2] = 0

def mailPST(mtype,sid,smid,name,dct):
    if mtype==1:
        subj = "【電算研】 書籍管理 利用者登録のお知らせ"
        with open("var/mail/m_newregist.html",mode="r",encoding="utf-8") as f:
            body = f.read().format(sid)
    elif mtype==2:
        subj = "【電算研】 書籍の 貸出/返却 が行われました"
        dtmp = list(zip(dct.keys(), dct.values()))
        dlist = ""
        for i in dtmp:
            dlist += "&raquo; {}まで / {} ({})<br>".format(
                dt.strptime(i[1],"%Y-%m-%d").strftime("%Y年 %m月 %d日"),
                EXT[0][i[0]],i[0])
        if len(dtmp) == 0 : dlist = "◎ 貸出はありません ◎<br>"
        with open("var/mail/m_updated.html",mode="r",encoding="utf-8") as f:
            body = f.read().format(name,dlist)
    elif mtype==3:
        subj = "【電算研】 書籍の 貸出期限 を過ぎています!!"
        with open("var/mail/m_delay.html",mode="r",encoding="utf-8") as f:
            body = f.read().format(name,dct)
    else:
        subj = -1; body = ""
    # .format caused css style error e.g. -> {width...
    with open("var/mail/m_style.html",mode="r",encoding="utf-8") as f:
        body += f.read()

    if smid == 1:
        to = "b{}@planet.kanazawa-it.ac.jp".format(sid)
    elif smid == 2:
        to = "c{}@planet.kanazawa-it.ac.jp".format(sid)
    elif smid == 3:
        to = "c{}@st.kanazawa-it.ac.jp".format(sid)
    else:
        to = -1

    mes = Mail(
        from_email = "<YOUR MAIL ADDR HERE>",
        to_emails = to,
        subject = subj,
        html_content = body)
    if not( subj == -1 or to == -1 ) : MAIL_Q.append(mes)

def mailAGT():
    global MAIL_Q
    while FLAG[0]:
        if len(MAIL_Q):
            try:
                if not(STID[0]) : upld_update("Mail sending...  Remain: {}".format(len(MAIL_Q))) 
                res = SendGridAPIClient("<INSERT API KEY HERE>").send(MAIL_Q[0])
                print("M{}: Mail send OK".format(res.status_code))
                MAIL_Q.pop()
            except Exception as e:
                if not(STID[0]) : upld_update("Mail send error! Retrying later...") 
                print("M.Err: {}".format(e))
                MAIL_Q.rotate(-1)
                slp(5)
        slp(2)

def pblcUPD():
    while FLAG[0]:
        while not(STID[0]) and PBD[1]:
            upld_update("Public Record Update...")
            try:
                with open("dict/public.csv",mode="w",encoding="cp932",newline="") as f:
                    wtr(f).writerows(list(zip(PBD[0].keys(), PBD[0].values())))
                upld_update("Public Record Update Done")
                PBD[1]=False
                RPTNUM[0]=RPTNUM[1] - len(PBD[0])
                slp(3)
                upld_update("Ready")
            except Exception as e:
                ex="P.Err: "+str(e)
                print(ex+"\n")
                stat_update(ftal,"[E17] 管理レコードを更新できません",
                        "管理者に連絡してください","\uea6a")
                upld_update("WARN: Public Record Error!")
                mplay("snd/crit.mp3")
                slp(5)
        slp(1)

#tk Alway update
def alway_update():
    global C_DATE
    if CNTDN[0]:
        if CNTDN[2] >= 10:
            CNTDN[2] = 0
            CNTDN[1] -= 1
            if CNTDN[1] <= 0 : CNTDN[0]=False
        countS.config(text=CNTDN[1])
        CNTDN[2]+=1 
    else:
        countS.config(text="")
    dateS.config(text=dt.now().strftime('%Y/%m/%d %H:%M:%S'))
    upldSR.config(text="{}/{}".format(RPTNUM[0],RPTNUM[1]))
    if C_DATE != dt.today().date():
        daily_update()
        C_DATE = dt.today().date()
    root.after(100,alway_update)

def daily_update():
    print( "> {} ---".format( dt.today().strftime("%Y/%m/%d") ) )
    stat_update(info,"KIT学生証をかざしてください",
                "返却日は {} です".format((dt.today()+td(days=CONFIG[2])).strftime("%Y/%m/%d") ),"\ued5c")
    # delay mail
    for i in EXT[1].keys():
        try:
            if pt.isfile("usr/{}.csv".format(i)):
                with open("usr/{}.csv".format(i),mode="r",encoding="cp932") as f:
                    tmpc = next(f).strip("\n").split(",")
                    tmpa = dt.today(); tmpd = ""
                    for row in rdr(f):
                        tmpb = dt.strptime(row[1],"%Y-%m-%d")
                        tmab = dt.date(tmpa) - dt.date(tmpb)
                        if  tmab.days == 1 or tmab.days % 7 == 0:
                            tmpd += "&raquo; {}まで / {} ({})<br>".format(
                                tmpb.strftime("%Y年 %m月 %d日"),EXT[0][row[0]],row[0])
                    if tmpd != "" :
                        mailPST(3, i, int(tmpc[1]), EXT[1][i], tmpd)
                        print(" - {} ------\n S: Delay Mail send OK \n".format(i))
        except Exception as e:
            print("S.Err: "+str(e))

    print("S: Daily update OK\n")

#Main label update
def stat_update(color,mes,mes2,icon):
    if not(FLAG[0]) : return
    statS.config(text=mes,bg=color)
    statF.config(bg=color)
    mainS.config(text=icon,bg=color)
    mainF.config(bg=color)
    isbnS.config(bg=color)
    statS2.config(text=mes2,bg=color)
#Sub label update
def upld_update(p1):
	if not(FLAG[0]) : return
	upldSL.config(text=p1)

# Frame init
titleF = tk.Frame(root)
titleF.pack(fill=tk.X)
countF = tk.Frame(titleF)
countF.pack(side=tk.RIGHT)

dateF = tk.Frame(root,bg=gray)
dateF.pack(side= tk.BOTTOM,fill=tk.X)

upldF = tk.Frame(root)
upldF.pack(side= tk.BOTTOM,fill=tk.X)
upldFR =tk.Frame(upldF,bg=gray)
upldFR.pack(side=tk.RIGHT)
upldFL =tk.Frame(upldF,bg=gray)
upldFL.pack(fill=tk.X)

statF = tk.Frame(root,bg=info)
statF.pack(side= tk.BOTTOM,fill=tk.X)

mainF = tk.Frame(root,bg=info)
mainF.pack(fill=tk.BOTH,expand=True)

# ラベル表示
titleS = tk.Label(titleF, text=(tx_title,tx_ver),
    font=("Segoe UI", "32"))
titleS.pack(side=tk.LEFT)

countS = tk.Label(countF, text=("99"),
    font=("Segoe UI", "32"))
countS.pack(side=tk.RIGHT)

dateS = tk.Label(dateF, text="----/--/-- --:--",
    font=("Consolas", "14"),
    fg=white,bg=gray)
dateS.pack(expand=True)

upldSL = tk.Label(upldFL, text="Startup...",
    font=("Consolas","14"),
    fg=white,bg=gray)
upldSL.pack(side=tk.LEFT)
upldSR = tk.Label(upldFR, text="---/---",
    font=("Consolas","14"),
    fg=white,bg=gray)
upldSR.pack(side=tk.RIGHT)

isbnS = tk.Entry(
    statF,font=("Consolas","14"),
    fg=white,bg=info,relief="flat",state=tk.DISABLED)
isbnS.pack(side=tk.BOTTOM,fill=tk.X)

statS2 = tk.Label(statF, text="お待ちください",
    font=("Segoe UI","18"),
    fg=white,bg=info)
statS2.pack(side=tk.BOTTOM,fill=tk.X)
statS = tk.Label(statF, text="起動中",
    font=("Segoe UI","24"),
    fg=white,bg=info)
statS.pack(expand=True)

mainS = tk.Label(mainF,text="\uf16a",
    font=("Segoe MDL2 Assets",220),
    fg=white,bg=info)
mainS.pack(expand=True)

try:
    with open("dict/master.csv") as f:
        next(f) #1行目スキップ
        for row in rdr(f):
            EXT[0] = {**EXT[0], row[0]:row[1]}
        RPTNUM[1]=len(EXT[0])
        print("F: Dict check OK")

    with open("dict/public.csv") as f:
        for row in rdr(f):
            PBD[0] = {**PBD[0], row[0]:row[1]}
        RPTNUM[0]=RPTNUM[1] - len(PBD[0])   
        print("F: Public check OK")

    with open("usr/master.csv") as f:
        for row in rdr(f):
            EXT[1] = {**EXT[1], row[0]:row[1]}
        print("F: User check OK")
except Exception as e:
        ex="S.Err: "+str(e)
        print(ex+"\n")
        exit()

# alway start
alway_update()

print("----------------\n")

# SYSTEM start
thr1 = th(target=dictSYS)
thr1.start()
thr2 = th(target=pblcUPD)
thr2.start()
thr3 = th(target=mailAGT)
thr3.start()

# Disp start
root.mainloop()

# shutdown
print("\n----------------")
print("Shutdown...")
print("Please disconnect NFC reader.")
FLAG[0] = False

thr2.join(); print("S: Public shutdown OK")
thr3.join(); print("S: Mail shutdown OK")
thr1.join(); print("S: NFC shutdown OK")

mx.quit()
print()