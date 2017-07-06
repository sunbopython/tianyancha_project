"""
    天眼查验证码采用网易触屏的geetest产品

    此脚本为具体破解实现，但是目前破解成功率有待提高，请谨慎使用

"""
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys  

import PIL.Image as Image
import PIL.ImageChops as imagechops
from urllib.request import urlopen
import time,re,random
import io

def get_merge_image(filename,location_list):
    '''
    根据位置对图片进行合并还原
    :filename:图片
    :location_list:图片位置
    '''
    pass

    im = Image.open(filename)

    new_im = Image.new('RGB', (260,116))

    im_list_upper=[]
    im_list_down=[]

    for location in location_list:

        if location['y']==-58:
            pass
            im_list_upper.append(im.crop((abs(location['x']),58,abs(location['x'])+10,166)))
        if location['y']==0:
            pass

            im_list_down.append(im.crop((abs(location['x']),0,abs(location['x'])+10,58)))

    new_im = Image.new('RGB', (260,116))

    x_offset = 0
    for im in im_list_upper:
        new_im.paste(im, (x_offset,0))
        x_offset += im.size[0]

    x_offset = 0
    for im in im_list_down:
        new_im.paste(im, (x_offset,58))
        x_offset += im.size[0]

    return new_im

def get_image(driver,div):
    '''
    下载并还原图片
    :driver:webdriver
    :div:图片的div
    '''
    pass

    #找到图片所在的div
    background_images=driver.find_elements_by_xpath(div)

    location_list=[]

    imageurl=''
    imageurl=re.findall("background-image: url\(\"(.*)\"\); background-position: (.*)px (.*)px;",background_images[0].get_attribute('style'))[0][0]

    for background_image in background_images:
        location={}
        
        #在html里面解析出小图片的url地址，还有长高的数值
        location['x']=int(re.findall("background-image: url\(\"(.*)\"\); background-position: (.*)px (.*)px;",background_image.get_attribute('style'))[0][1])
        location['y']=int(re.findall("background-image: url\(\"(.*)\"\); background-position: (.*)px (.*)px;",background_image.get_attribute('style'))[0][2])
        location_list.append(location)

    #jpgfile=io.BytesIO(urlopen(imageurl).read())   # too slow here
    # 从浏览器cache中获取图片    
    driver.execute_script("window.open('{}','new_window')".format(imageurl))
    driver.switch_to_window(driver.window_handles[1])
    print("Current url is:{}",driver.current_url)
    imagename=imageurl.replace("webp","jpg").split("/")[-1]
    driver.save_screenshot(imagename)

    # crop screensh
    im = Image.open(imagename)
    im_small = im.crop((0,0,312,116))
    im_small.save(imagename)
    driver.close()
    driver.switch_to_window(driver.window_handles[0])



    #Locate Image
    #Image = driver.find_element_by_xpath("//img")
    #action = ActionChains(driver)
    #action.context_click(Image)
    #action.send_keys(Keys.ARROW_DOWN) 
    #action.send_keys('v')
    #action.perform()

    #imgByteArr =io.BytesIO()
    #roiImg.save(imgByteArr,format='png')
    #imgByteArr =imgByteArr.getvalue()
    #jpgfile = io.BytesIO(jpgfile)
    
    #driver.close()    # close the tab


    #重新合并图片 
    image=get_merge_image(imagename,location_list )
    #image=get_merge_image(jpgfile,location_list )

    return image


def is_similar(image1,image2,x,y):
    '''
    对比RGB值
    '''
    pass

    pixel1=image1.getpixel((x,y))
    pixel2=image2.getpixel((x,y))

    for i in range(0,3):
        if abs(pixel1[i]-pixel2[i])>=50:
            return False

    return True

def get_diff_location(image1,image2):
    '''
    计算缺口的位置
    '''

    i=0

    for i in range(0,260):
        for j in range(0,116):
            if is_similar(image1,image2,i,j)==False:
                return  i

def get_track(length):
    '''
    根据缺口的位置模拟x轴移动的轨迹
    '''
    pass

    list=[]

#     间隔通过随机范围函数来获得
    x=random.randint(1,3)

    while length-x>=5:
        list.append(x)

        length=length-x
        x=random.randint(1,3)

    for i in range(length):
        list.append(1)

    return list


def main():

#     这里的文件路径是webdriver的文件路径
    options = webdriver.ChromeOptions()
    options.add_argument("applicationCacheEnabled=True")
    driver = webdriver.Chrome(executable_path=r"C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe",chrome_options=options)

#     打开网页
    #driver.get("http://192.168.10.11:8000/")
    #driver.get("localhost:8000/")
    driver.get("http://antirobot.tianyancha.com/captcha/verify?return_url=http://www.tianyancha.com/company/22822")

#     等待页面的上元素刷新出来
    WebDriverWait(driver, 30).until(lambda the_driver: the_driver.find_element_by_xpath("//div[@class='gt_slider_knob gt_show']").is_displayed())
    WebDriverWait(driver, 30).until(lambda the_driver: the_driver.find_element_by_xpath("//div[@class='gt_cut_bg gt_show']").is_displayed())
    WebDriverWait(driver, 30).until(lambda the_driver: the_driver.find_element_by_xpath("//div[@class='gt_cut_fullbg gt_show']").is_displayed())

#     下载图片
    image1=get_image(driver, "//div[@class='gt_cut_bg gt_show']/div")
    image2=get_image(driver, "//div[@class='gt_cut_fullbg gt_show']/div")

#     计算缺口位置
    loc=get_diff_location(image1, image2)

#     生成x的移动轨迹点
    track_list=get_track(loc)
    print(track_list)

#     找到滑动的圆球
    element=driver.find_element_by_xpath("//div[@class='gt_slider_knob gt_show']")
    location=element.location
#     获得滑动圆球的高度
    y=location['y']

#     鼠标点击元素并按住不放
    print("第一步,点击元素")
    ActionChains(driver).click_and_hold(on_element=element).perform()
    time.sleep(0.25)

    print("第二步，拖动元素")
    track_string = ""
    track_len = len(track_list)
    for num,track in enumerate(track_list):
        track_string = track_string + "{%d,%d}," % (track, y - 445)
#         xoffset=track+22:这里的移动位置的值是相对于滑动圆球左上角的相对值，而轨迹变量里的是圆球的中心点，所以要加上圆球长度的一半。
#         yoffset=y-445:这里也是一样的。不过要注意的是不同的浏览器渲染出来的结果是不一样的，要保证最终的计算后的值是22，也就是圆球高度的一半
        ActionChains(driver).move_to_element_with_offset(to_element=element, xoffset=track+22, yoffset=y-445).perform()
        # 间隔时间也通过随机函数来获得
        # 前半部分快，后半部分慢
        if num/track_len<0.50:
            time.sleep(random.randint(1,10)/1000)
        elif num/track_len<=0.70 and num/track_len>=0.50:
            time.sleep(random.randint(5,15)/1000)
        else:
            time.sleep(random.randint(15,100)/1000)

    print(track_string)
#     xoffset=21，本质就是向后退一格。这里退了5格是因为圆球的位置和滑动条的左边缘有5格的距离
    ActionChains(driver).move_to_element_with_offset(to_element=element, xoffset=21, yoffset=y-445).perform()
    time.sleep(0.1)
    ActionChains(driver).move_to_element_with_offset(to_element=element, xoffset=21, yoffset=y-445).perform()
    time.sleep(0.1)
    ActionChains(driver).move_to_element_with_offset(to_element=element, xoffset=21, yoffset=y-445).perform()
    time.sleep(0.1)
    ActionChains(driver).move_to_element_with_offset(to_element=element, xoffset=21, yoffset=y-445).perform()
    time.sleep(0.1)
    ActionChains(driver).move_to_element_with_offset(to_element=element, xoffset=21, yoffset=y-445).perform()

    print("第三步，释放鼠标")
#     释放鼠标
    ActionChains(driver).release(on_element=element).perform()

    time.sleep(3)

#     点击验证
    submit=driver.find_element_by_xpath("//button[@id='submit-button']")
    ActionChains(driver).click(on_element=submit).perform()

    time.sleep(5)

    driver.quit()

if __name__ == '__main__':
    pass

    main()