# -*- coding: utf-8 -*-
import os
import sqlite3

from PySide import QtCore, QtGui
from PySide.QtUiTools import QUiLoader

import ImageScene

#GUIを作る
class GUI(QtGui.QMainWindow):
    
    def __init__(self, parent=None):
        super(GUI, self).__init__(parent)
        loader = QUiLoader()
        uiFilePath = 'MainWindow.ui'
        self.UI = loader.load(uiFilePath) #UIのロード
        self.setCentralWidget(self.UI)
        
        #シグナルの追加
        self.setSignals()
 
      
        #QtImageViewの初期設定
        #QGraphicsViewの設定
        self.GViews = [self.UI.graphicsView_ImageType1, self.UI.graphicsView_ImageType2]      
        
        #QGraphicsSceneの生成
        self.Scenes = [ ImageScene.ImageScene(self.UI.graphicsView_ImageType1), ImageScene.ImageScene(self.UI.graphicsView_ImageType2) ]
        for scene, GView in zip(self.Scenes, self.GViews):
            scene.setSceneRect(QtCore.QRectF(self.rect()))
            scene.installEventFilter(self)
            GView.setScene(scene)
        
        
        #その他パラメータの初期値設定
        self.Label_Rect = []
        self.MousePressed = False #マウスが押されているかのフラグ
        self.isSetRectangle = False #矩形が選択済みかのフラグ
        self.LabelList = [ self.UI.comboBox_SetLabelName.itemText(v) for v in range(self.UI.comboBox_SetLabelName.count())]
        self.DeleteFlag = False #矩形をリセットするかのフラグ

            
    #シグナルの追加
    def setSignals(self):
        #ボタンのクリック
        self.UI.pushButton_SetRootFolder.clicked.connect(self.SetRootFolder) #ルートフォルダの設定ボタン
        self.UI.pushButton_SetWorkFolder.clicked.connect(self.SetWorkFolder) #作業フォルダの設定ボタン
        self.UI.pushButton_ReadImages.clicked.connect(self.ReadImages) #画像読み込みボタン
        self.UI.pushButton_LoadPrev.clicked.connect(self.LoadPrev) #前の画像ボタン
        self.UI.pushButton_LoadNext.clicked.connect(self.LoadNext) #次の画像ボタン
        self.UI.pushButton_SaveRectangle.clicked.connect(self.SaveRectangle) #矩形の保存ボタン
        self.UI.pushButton_ResetRectangles.clicked.connect(self.ResetRectangles) #矩形のリセットボタン
        
        #リストウィンドウのクリック
        self.UI.listView_FileList.clicked.connect(self.ListClicked)
 
       
    #フォルダエラーのチェック
    def CheckFolderEnvironment(self):
        #エラーチェック
        if not 'RootDir_path' in dir(self) or not 'WorkDir_relpath' in dir(self):
            msgBox = QtGui.QMessageBox()
            msgBox.setText(u"作業用フォルダが適切に設定されていません")
            msgBox.exec_()
            return False
        return True
    
    
    #----------
    #作業環境のセットアップ
    #----------
    
    #ルートディレクトリをセット
    def SetRootFolder(self):
        self.RootDir_path = QtGui.QFileDialog.getExistingDirectory(self, u'ルートフォルダを選択', './')
        self.UI.lineEdit_ShowRootFolder.setText(self.RootDir_path)
        
        #データベースのセットアップ
        self.dbname = 'LabeledImageDatabase.db' #データベース名
        con = sqlite3.connect( os.path.join(self.RootDir_path, self.dbname) )
        cur = con.cursor()
        #テーブルの重複確認
        for label in self.LabelList:
            cur.execute( "SELECT * FROM sqlite_master WHERE type='table' and name='Labels'" )
            if cur.fetchone() == None:
                cur.execute("CREATE TABLE Labels (label text, filename text, x integer, y integer, width integer, height integer)")
                con.commit()
        con.close()
        
    
    #作業ディレクトリをセット
    def SetWorkFolder(self):
        #エラーチェック
        if not 'RootDir_path' in dir(self):
            msgBox = QtGui.QMessageBox()
            msgBox.setText(u"ルートフォルダが指定されていません")
            msgBox.exec_()
            return
            
            
        self.WorkDir_relpath = QtGui.QFileDialog.getExistingDirectory(self, u'作業フォルダを選択', self.RootDir_path)
        self.WorkDir_relpath = os.path.relpath(self.WorkDir_relpath, start=self.RootDir_path)
        self.UI.lineEdit_ShowWorkFolder.setText(self.WorkDir_relpath)
    
    
    #----------
    #イベント処理
    #----------

    #イベントのキャッチ
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.GraphicsSceneMousePress:
            #マウスがクリックされた時
            e = event.scenePos()
            self.MouseClicked(e.x(), e.y())
            self.MousePressed = True
            return True
        
        if event.type() == QtCore.QEvent.GraphicsSceneMouseRelease:
            #マウスが離された時
            e = event.scenePos()
            self.MouseReleased(e.x(), e.y())
            self.MousePressed = False
            return True
            
        if event.type() == QtCore.QEvent.GraphicsSceneMouseMove and self.MousePressed:
            #マウスがドラッグされてる時
            e = event.scenePos()
            self.MouseMoving(e.x(), e.y())
            return True
        
        return False


    #画像の上でマウスが押された
    def MouseClicked(self, x, y):
        #座標の有効性チェック
        if x < 0 : x = 0
        if y < 0 : y = 0
        if x > self.Scenes[0].imageItem.boundingRect().width(): x = self.Scenes[0].imageItem.boundingRect().width()
        if y > self.Scenes[0].imageItem.boundingRect().height(): y = self.Scenes[0].imageItem.boundingRect().height()

        if len(self.Label_Rect) <= 1:
            self.Label_Rect.append([int(x), int(y)])
        else:                  
            self.Label_Rect[0][0] = int(x)
            self.Label_Rect[0][1] = int(y)

        
    #画像の上でマウスが離された   
    def MouseReleased(self, x, y):        
        #座標の有効性チェック
        if x < 0 : x = 0
        if y < 0 : y = 0
        if x > self.Scenes[0].imageItem.boundingRect().width(): x = self.Scenes[0].imageItem.boundingRect().width()
        if y > self.Scenes[0].imageItem.boundingRect().height(): y = self.Scenes[0].imageItem.boundingRect().height()
       
        #座標の更新 
        if len(self.Label_Rect) <= 1:
            self.Label_Rect.append([int(x), int(y)])
        else:
            self.Label_Rect[1][0] = int(x)
            self.Label_Rect[1][1] = int(y)
        
        #矩形座標リストの形式を(左上,左下)に揃える
        if self.Label_Rect[1][0] < self.Label_Rect[0][0]:
            lr = self.Label_Rect[1][0]
            self.Label_Rect[1][0] = self.Label_Rect[0][0]
            self.Label_Rect[0][0] = lr
            
        elif self.Label_Rect[1][1] < self.Label_Rect[0][1]:
            lr = self.Label_Rect[1][1]
            self.Label_Rect[1][1] = self.Label_Rect[0][1]
            self.Label_Rect[0][1] = lr
        
        #選択された矩形表示の更新
        self.CurrentLabel = self.UI.comboBox_SetLabelName.currentText()
        s = "Label = " + self.CurrentLabel + ", Rectangle = " + str(self.Label_Rect[0][0]) + ", " + str(self.Label_Rect[0][1]) + ", " + str(self.Label_Rect[1][0]-self.Label_Rect[0][0]) + ", " + str(self.Label_Rect[1][1]-self.Label_Rect[0][1])
        self.UI.lineEdit_ShowSelectedRectangle.setText(s)
        self.UpdateImages(self.Label_Rect)        
        
        self.isSetRectangle = True

                
    #画像の上をマウスがドラッグ中
    def MouseMoving(self, x, y):
        #座標の有効性チェック
        if x < 0 : x = 0
        if y < 0 : y = 0
        if x > self.Scenes[0].imageItem.boundingRect().width(): x = self.Scenes[0].imageItem.boundingRect().width()
        if y > self.Scenes[0].imageItem.boundingRect().height(): y = self.Scenes[0].imageItem.boundingRect().height()
              
        if len(self.Label_Rect) <= 1:
            self.Label_Rect.append([int(x), int(y)])
        else:                  
            self.Label_Rect[1][0] = int(x)
            self.Label_Rect[1][1] = int(y)
        
        self.UpdateImages(self.Label_Rect)


    #----------
    #画像の表示・切り替え処理
    #----------
    
    #画像をロード
    def ReadImages(self):
        #エラーチェック
        if not self.CheckFolderEnvironment():
            return
        
        #画像タイプの取得(初期設定ではIRとRGB)
        self.ImageTypeName = [ self.UI.lineEdit_ImageTypeName1.text(), self.UI.lineEdit_ImageTypeName2.text() ]            
        
        #フォルダ指定のエラーチェック
        if os.path.exists( os.path.join(self.RootDir_path, self.WorkDir_relpath, self.ImageTypeName[0]) ) and os.path.exists( os.path.join(self.RootDir_path, self.WorkDir_relpath, self.ImageTypeName[1]) ):
            
            #フォルダ内のファイルリストを取得
            files = []
            for filename in os.listdir( os.path.join(self.RootDir_path, self.WorkDir_relpath, self.ImageTypeName[0]) ):
                #jpegファイルだけ受付
                if filename.endswith('.jpg'):
                    files.append(filename)
            
            #取得したファイル一覧をソート
            files = [ os.path.splitext(f) for f in files ] #ファイル名は文字列なので拡張子とファイル番号を切り分けて
            files = sorted(files, key=lambda x: int(x[0])) #ファイル番号をint型の数値としてソート
            files = [ f[0]+f[1] for f in files] #拡張子と合体してファイル名を元に戻す
            self.FileList = files
            
        else:
            msgBox = QtGui.QMessageBox()
            msgBox.setText(u"指定されたフォルダが有効ではありません. 確認してください.")
            msgBox.exec_()
            return
        
        #画像一覧の更新
        ListModel = QtGui.QStringListModel(self.FileList)
        self.UI.listView_FileList.setViewMode(QtGui.QListView.ListMode)
        self.UI.listView_FileList.setModel(ListModel)
        
        #画像タイプの表示更新
        
        self.UI.label_ShowImageType1.setText(self.ImageTypeName[0])
        self.UI.label_ShowImageType2.setText(self.ImageTypeName[1])
        
        self.CurrentFileIndex = 0
        self.SetImages(self.FileList[0])

        
    #画像の表示    
    def SetImages(self, fname):
        imagePath = [os.path.join(self.RootDir_path, self.WorkDir_relpath, v, fname) for v in self.ImageTypeName]
        self.CheckRectangle()
        
        for GView, scene, path in zip(self.GViews, self.Scenes, imagePath):
            scene.setFile(path)
            scene.setRectangleFromDatabase(self.RectangleFromDatabase, self.LabelFromDatabase)
            GView.setScene(scene)
            self.UI.lineEdit_ShowFileName.setText(self.FileList[self.CurrentFileIndex])
 
                       
    #画像の更新
    def UpdateImages(self, Rect):
        for GView, scene in zip(self.GViews, self.Scenes):
            scene.setRectangle(Rect, self.UI.comboBox_SetLabelName.currentText())
            GView.setScene(scene)
            self.UI.lineEdit_ShowFileName.setText(self.FileList[self.CurrentFileIndex])
 
    #データベース内に過去に登録された他の矩形がないかを探す   
    def CheckRectangle(self):
        con = sqlite3.connect(os.path.join(self.RootDir_path, self.dbname))
        sql = "select x, y, width, height, label from Labels where filename = ?"
        val = ( self.FileList[self.CurrentFileIndex], )
        cur = con.execute(sql, val)
        
        self.RectangleFromDatabase = []
        self.LabelFromDatabase = []
        for row in cur:
            self.RectangleFromDatabase.append([ row[0], row[1], row[0]+row[2], row[1]+row[3] ])
            self.LabelFromDatabase.append(row[4])
        
        con.close()


    #ファイルリストからファイルが選択されたらその画像に切り替える  
    def ListClicked(self):
        if self.CurrentFileIndex != self.UI.listView_FileList.selectedIndexes()[0].row():
            self.CurrentFileIndex = self.UI.listView_FileList.selectedIndexes()[0].row()
            self.SetImages(self.FileList[self.CurrentFileIndex])
  
      
    #次の画像を読み込む
    def LoadNext(self):
        #エラーチェック
        if not self.CheckFolderEnvironment():
            return
        
        if self.CurrentFileIndex < len(self.FileList)-1:
            self.CurrentFileIndex += 1
            self.SetImages(self.FileList[self.CurrentFileIndex])
        else:
            msgBox = QtGui.QMessageBox()
            msgBox.setText(u"最後のファイルです")
            msgBox.exec_()
            return
   
   
    #前の画像を読み込む    
    def LoadPrev(self):
        #エラーチェック
        if not self.CheckFolderEnvironment():
            return
        
        if self.CurrentFileIndex > 0:
            self.CurrentFileIndex -= 1
            self.SetImages(self.FileList[self.CurrentFileIndex])
        else:
            
            msgBox = QtGui.QMessageBox()
            msgBox.setText(u"最初のファイルです")
            msgBox.exec_()
            return


    #----------
    #ラベル矩形の保存処理
    #----------
    
    #矩形をデータベースに保存
    def SaveRectangle(self):
        #エラーチェック
        if not self.CheckFolderEnvironment():
            return
        
        if self.isSetRectangle:
            #矩形の保存
            con = sqlite3.connect(os.path.join(self.RootDir_path, self.dbname))
            sql = "insert into Labels (label, filename, x, y, width, height) values (?, ?, ?, ?, ?, ?)"
            val = (self.CurrentLabel, self.FileList[self.CurrentFileIndex], self.Label_Rect[0][0], self.Label_Rect[0][1], self.Label_Rect[1][0]-self.Label_Rect[0][0], self.Label_Rect[1][1]-self.Label_Rect[0][1] )
            con.execute(sql, val)
            con.commit()
            con.close()
            
            self.SetImages(self.FileList[self.CurrentFileIndex])
            self.UI.lineEdit_ShowSelectedRectangle.setText(u"矩形が保存されました")
            self.isSetRectangle = False
        else:
            self.UI.lineEdit_ShowSelectedRectangle.setText(u"矩形が選択されていません")
            return
    
    
    #この画像に登録されている矩形をすべて削除
    def ResetRectangles(self):
        #エラーチェック
        if not self.CheckFolderEnvironment():
            return
        
        if self.DeleteFlag:
            #矩形の削除
            con = sqlite3.connect(os.path.join(self.RootDir_path, self.dbname))
            sql = "delete from Labels where filename = ?"
            val = ( self.FileList[self.CurrentFileIndex], )
            con.execute(sql, val)
            con.commit()
            con.close()
            
            self.SetImages(self.FileList[self.CurrentFileIndex])
            self.UI.lineEdit_ShowSelectedRectangle.setText(u"矩形が削除されました")
            
            self.DeleteFlag = False
        
        else:
            self.UI.lineEdit_ShowSelectedRectangle.setText(u"本当に削除してもよろしいですか？ 削除する場合はもう一度押してください")
            self.DeleteFlag = True



if __name__ == '__main__':
    app = QtGui.QApplication.instance()
    ui = GUI()
    ui.show()
