import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1200  # ゲームウィンドウの幅
HEIGHT = 600  # ゲームウィンドウの高さ
MAIN_DIR = os.path.split(os.path.abspath(__file__))[0]


def check_bound(obj: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内か画面外かを判定し，真理値タプルを返す
    引数 obj：オブジェクト（爆弾，こうかとん，ビーム）SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj.left < 0 or WIDTH < obj.right:  # 横方向のはみ出し判定
        yoko = False
    if obj.top < 0 or HEIGHT < obj.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
        pg.K_LSHIFT: (0,0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"{MAIN_DIR}/fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
 
        self.state ="normal"
        self.hyper_life = 0

    

 

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"{MAIN_DIR}/fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        if key_lst[pg.K_LSHIFT]:
            self.speed = 20
    
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]


        if check_bound(self.rect) != (True, True):
            for k, mv in __class__.delta.items():
                if key_lst[k]:
                    self.rect.move_ip(-self.speed*mv[0], -self.speed*mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        if self.state == "hyper": #無敵状態だったら
            self.image = pg.transform.laplacian(self.image)
            self.hyper_life -= 1
        if self.hyper_life < 0:
            self.state ="normal"
        screen.blit(self.image, self.rect)

        

    # #def Muteki(self,key_lst:list[bool],screen: pg.Surface): #無敵状態
    #     score = Score()
    #     if key_lst[pg.K_RSHIFT] and score.value > 1 and self.state == "normal":
    #         self.state ="hyper"
    #         self.hyper_life = 500
    #     if self.state == "hyper":
    #         self.image = pg.transform.laplacian(self.image)
    #         screen.blit(self.image)
    #         self.hyper_life -= 1
    #     if self.hyper_life < 0:
    #         self.state ="normal"        

class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        self.image = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height/2
        self.speed = 6
        self.state = "active"

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    
    def __init__(self, bird: Bird, angle0: float=0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))+angle0
        self.image = pg.transform.rotozoom(pg.image.load(f"{MAIN_DIR}/fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10
    

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class NeoBeam:
    def __init__(self, bird: Bird, num: int):
        self.bird = bird
        self.num = num

    def generate_beams(self) -> list[Beam]:
        #step = 50 if num_beams == 3 else 25
        #angles = range(-50, +51, 50)
        #beams = [Beam(bird, angle) for angle in angles]
        return [Beam(self.bird, angle) for angle in range(-50, +51, int(100/(self.num-1)))]

class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"{MAIN_DIR}/fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"{MAIN_DIR}/fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vy = +6
        self.bound = random.randint(50, HEIGHT/2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy


class EMP(pg.sprite.Sprite):
    """
    電磁パルスに関するクラス
    """
    def __init__(self, emys, bombs, screen):
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT))
        pg.draw.rect(self.image, (255, 255, 0), (0, 0, WIDTH, HEIGHT))
        self.image.set_alpha(128)
        self.rect = self.image.get_rect()
        screen.blit(self.image, self.rect)
        pg.display.update()
        time.sleep(0.05)
        for emy in emys:
            emy.interval = math.inf
            emy.image = pg.transform.laplacian(emy.image)
            emy.image.set_colorkey((0, 0, 0))
        for bomb in bombs:
            bomb.speed /= 2
            bomb.state = "inactive"



class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    
    def __init__(self):
        self.value = 0
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class Gravity(pg.sprite.Sprite):
    """
    <追加機能2>
    画面全体を覆う重力場を発生させる
    画面全体を覆う重力場を派生させるクラス
    重力場：画面全体に透明度のある黒い矩形
    発動時間：400フレーム
    効果：重力球の範囲内の爆弾を打ち落とす
    発動条件：リターンキー押下，かつ，スコアが200より大
    消費スコア：200
    """
    def __init__(self, life: int):
        super().__init__()
        self.life = life
        self.image = pg.Surface((WIDTH, HEIGHT))  # 空のSurfaceインスタンスを生成
        self.rect = self.image.get_rect()
        pg.draw.rect(self.image,[0, 0, 0],(0, 0, WIDTH, HEIGHT))  # 上記Surfaceにrectをdrawする
        self.image.set_alpha(128)  # 重力場の透明度を設定(半透明：128)
        

    def update(self,screen:pg.Surface):
        self.life -= 1
        if self.life < 0:
            self.kill()
        screen.blit(self.image, self.rect)
        

def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"{MAIN_DIR}/fig/pg_bg.jpg")
    score = Score()

    score.update(screen)#スコアの表示

    speed = 10

 
    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    gravities = pg.sprite.Group()  # Gravityグループを作成

    tmr = 0
    clock = pg.time.Clock()

    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
 
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE and key_lst[pg.K_LSHIFT]:
                beams.add(NeoBeam(bird, 5).generate_beams())
            elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_LSHIFT:
                speed*2 
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
 
            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT:
                if score.value > 1:
                    bird.state = "hyper"
                    bird.hyper_life = 500
                    score.value -= 100

 
            if event.type == pg.KEYDOWN and event.key == pg.K_e:
                if score.value >= 20 :
                    emp = EMP(emys, bombs, screen)
                    score.value -= 20

            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN and score.value >= 200:  # リターンキーが押され、スコアが200以上のとき
                    gravities.add(Gravity(400))  
                    score.value -= 200  # スコアを200減らす
                    # 重力場と爆弾の衝突判定
                    for bomb in pg.sprite.groupcollide(bombs, gravities, True, False).keys():
                        exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                        score.value += 1  # 1点アップ

                    # 重力場と敵機の衝突判定
                    for emy in pg.sprite.groupcollide(emys, gravities, True, False).keys():
                        exps.add(Explosion(emy, 100))  # 爆発エフェクト
                        score.value += 10  # 10点アップ

 

        screen.blit(bg_img, [0, 0])
 

        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        #無敵状態で爆弾にぶつかる
        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

 
        # bird.Muteki(key_lst, screen)
        for bomb in pg.sprite.spritecollide(bird, bombs, True):
            if bird.state =="normal":
                bird.change_img(8, screen)

        for bomb in pg.sprite.spritecollide(bird, bombs, True):
            if bomb.state == "active":
                bird.change_img(8, screen) # こうかとん悲しみエフェクト
 
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
 
            if bird.state == "hyper":
                exps.add(Explosion(bomb, 50))
                score.value += 1
        
        screen.blit(bg_img, [0, 0])


 main
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        score.update(screen)
        gravities.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
