# -*- coding: utf-8 -*-
import cv2
from PySide import QtGui

#画像処理・表示用のSceneクラス
class ImageScene(QtGui.QGraphicsScene):
    imageItem = None
    rectItem = None
    
    def __init__(self, *argv, **keywords):
        super(ImageScene, self).__init__(*argv, **keywords)
    
    #画像をセット
    def setFile(self, filepath):
        im = cv2.imread(filepath)
        
        if im == None:
            msgBox = QtGui.QMessageBox()
            msgBox.setText(u"画像が読み込めません")
            msgBox.exec_()
            return
        
        self.input_image = im.copy()        
        
        #opencvの読み込み画像形式からQtGuiで扱える形式に変換
        pixmap = self.imageConvert_CV2QT(im)
        
        self.UpdateScene(pixmap)

    #OpenCVの画像形式からQtGuiで扱える画像形式に変換
    def imageConvert_CV2QT(self, im):
        im = cv2.cvtColor(im,cv2.COLOR_BGR2RGB)
        height, width, dim = im.shape
        bytesPerLine = dim*width
        qImage = QtGui.QImage(im.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qImage)
        
        return pixmap
    
    def UpdateScene(self, pixmap):
        #すでに画像があれば消して置き換える
        if self.imageItem:
            self.removeItem(self.imageItem)
        
        #画像をシーンに追加
        item = QtGui.QGraphicsPixmapItem(pixmap)
        item.setZValue(1)
        self.addItem(item)
        self.imageItem = item

    #矩形の描画
    def setRectangle(self, rect, label):
        #OpenCVで読み込んだ画像を持ってるほうがなにかと便利
        im = self.input_image.copy()
        
        im = cv2.rectangle(im, (int(rect[0][0]), int(rect[0][1])), (int(rect[1][0]), int(rect[1][1])),(0,255,0),1)
        im = cv2.putText(im, label, (int(rect[0][0]), int(rect[0][1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0))       
        
        pixmap = self.imageConvert_CV2QT(im)
        self.UpdateScene(pixmap)
    
    #データベースから読み込んだ矩形を描画
    def setRectangleFromDatabase(self, rects, labels):
        im = self.input_image.copy()
        
        for rect, label, in zip(rects, labels):
            im = cv2.rectangle(im, (int(rect[0]), int(rect[1])), (int(rect[2]), int(rect[3])),(0,255,0),1)
            im = cv2.putText(im, label, (int(rect[0]), int(rect[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0))
        
        self.input_image = im.copy()
        
        pixmap = self.imageConvert_CV2QT(im)
        self.UpdateScene(pixmap)