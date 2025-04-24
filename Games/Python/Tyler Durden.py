import pygame
import random
import math
import os



pygame.init()
SW, SH = 800, 600
WW, WH = 3000, 3000
FPS = 60
W = (255, 255, 255)
D = pygame.display.set_mode((SW, SH))
C = pygame.time.Clock()

def coll(x1,y1,r1,x2,y2,r2):
    return math.hypot(x1-x2,y1-y2)<r1+r2




class B:
    def __init__(s,x,y,r,col):
        s.x=x
        s.y=y
        s.r=r
        s.c=col
    def d(s,S,cx,cy):
        xx=int(s.x-cx)
        yy=int(s.y-cy)
        pygame.draw.circle(S,s.c,(xx,yy),int(s.r))




class P(B):
    def __init__(s,x,y):
        super().__init__(x,y,20,(0,0,255))
        s.s=5
        s.org=pygame.image.load("/Users/marioamitrano/Desktop/Baker-FightClub.jpg.webp").convert_alpha()
    def u(s,k):
        dx,dy=0,0
        if k[pygame.K_LEFT] or k[pygame.K_a]:dx=-1
        if k[pygame.K_RIGHT] or k[pygame.K_d]:dx=1
        if k[pygame.K_UP] or k[pygame.K_w]:dy=-1
        if k[pygame.K_DOWN] or k[pygame.K_s]:dy=1
        s.x+=dx*s.s
        s.y+=dy*s.s
        s.x=max(s.r,min(WW-s.r,s.x))
        s.y=max(s.r,min(WH-s.r,s.y))
    def d(s,S,cx,cy):
        xx=int(s.x-cx-s.r)
        yy=int(s.y-cy-s.r)
        im=pygame.transform.smoothscale(s.org,(int(s.r*2),int(s.r*2)))
        S.blit(im,(xx,yy))



class E(B):
    def __init__(s,x,y,r):
        col=random.choice([(255,0,0),(0,255,0),(255,255,0),(128,0,128),(0,255,255),(255,165,0)])
        super().__init__(x,y,r,col)
        s.sp=random.uniform(1,3)
        s.di=random.uniform(0,2*math.pi)
    def u(s):
        s.x+=s.sp*math.cos(s.di)
        s.y+=s.sp*math.sin(s.di)
        if s.x-s.r<0 or s.x+s.r>WW:s.di=math.pi-s.di
        if s.y-s.r<0 or s.y+s.r>WH:s.di=-s.di



class G:
    def __init__(s):
        pygame.display.set_caption("Game")
        s.p=P(WW/2,WH/2)
        s.e=[]
        s.n=70
        for _ in range(s.n):
            r=random.randint(10,30)
            x=random.randint(r,WW-r)
            y=random.randint(r,WH-r)
            s.e.append(E(x,y,r))
        s.r=True
        s.f=pygame.font.SysFont(None,24)
        s.sc=0
        s.t=0
    def sp(s):
        r=random.randint(10,20)
        x=random.randint(r,WW-r)
        y=random.randint(r,WH-r)
        s.e.append(E(x,y,r))
    def h(s):
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT:s.r=False
    def u(s):
        k=pygame.key.get_pressed()
        s.p.u(k)
        for en in s.e:en.u()
        rm=[]
        for en in s.e:
            if coll(s.p.x,s.p.y,s.p.r,en.x,en.y,en.r):
                if s.p.r>en.r:
                    grow_target = math.sqrt(s.p.r**2 + en.r**2)
                    diff = grow_target - s.p.r
                    s.p.r += 0.34 * diff
                    s.sc+=1
                    rm.append(en)
                elif en.r> s.p.r:
                    s.r=False
        for en in rm:
            if en in s.e:
                s.e.remove(en)
                s.sp()
        ec=s.e.copy()
        for i in range(len(ec)):
            for j in range(i+1,len(ec)):
                e1=ec[i]
                e2=ec[j]
                if e1 not in s.e or e2 not in s.e:continue
                if coll(e1.x,e1.y,e1.r,e2.x,e2.y,e2.r):
                    if e1.r>e2.r:
                        e1.r=math.sqrt(e1.r**2+e2.r**2)
                        if e2 in s.e:
                            s.e.remove(e2)
                            s.sp()
                    elif e2.r>e1.r:
                        e2.r=math.sqrt(e2.r**2+e1.r**2)
                        if e1 in s.e:
                            s.e.remove(e1)
                            s.sp()
        s.t+=1
        if s.t>=FPS*5:
            s.sp()
            s.t=0



    def cam(s):
        cx=s.p.x-SW/2
        cy=s.p.y-SH/2
        cx=max(0,min(WW-SW,cx))
        cy=max(0,min(WH-SH,cy))
        return cx,cy
    


    def d(s):
        t=pygame.time.get_ticks()/1000
        c=int(20+20*math.sin(t))
        D.fill((c,c,c))
        cx,cy=s.cam()
        s.p.d(D,cx,cy)
        for en in s.e:en.d(D,cx,cy)
        st=s.f.render("Score: "+str(s.sc),True,W)
        D.blit(st,(10,10))
        pygame.display.flip()



    def run(s):
        while s.r:
            C.tick(FPS)
            s.h()
            s.u()
            s.d()
        pygame.quit()




if __name__=="__main__":
    G().run()
