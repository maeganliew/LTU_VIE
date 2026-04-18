from direct.showbase.ShowBase import ShowBase
from panda3d.core import CardMaker

class Renderer(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        cm = CardMaker("card")
        cm.setFrame(-1, 1, -1, 1)
        card = self.render.attachNewNode(cm.generate())
        card.setColor(1, 0, 0, 1)
        card.setTwoSided(True)
        card.setLightOff()
        self.camera.setPos(0, -3, 0)
        self.camera.lookAt(0, 0, 0)

Renderer().run()