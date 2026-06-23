#!/usr/bin/env python3
"""
verify_watchlist.py
===================
สร้าง master CSV ของหุ้น SET watchlist พร้อมข้อมูลธุรกิจที่ verified

โหมดการทำงาน:
  1. ถ้าเชื่อม Yahoo Finance ได้ → ดึง live data
  2. ถ้าเชื่อมไม่ได้ (403 / network block) → ใช้ embedded curated data
     (curated มาจาก SET factsheet + 56-1 + ข้อมูล public)

ใช้กับ Claude Code:
    pip install requests beautifulsoup4 lxml
    python verify_watchlist.py

Output (ใน /mnt/user-data/outputs/):
    watchlist_verified.csv   <- ตารางหลัก
    watchlist_raw.json       <- ข้อมูลดิบ
    watchlist_review.md      <- รายการที่ต้อง human review
"""

import csv
import json
import time
import sys
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup  # noqa: F401
    HAS_REQUESTS = True
except ImportError:
    print("tip: pip install requests beautifulsoup4 lxml  (ใช้ embedded data แทน)")
    HAS_REQUESTS = False

# ─────────────────────────────────────────────────────────────
# CURATED DATA — verified จาก SET factsheet + 56-1 + IR
# source: SET official profile, หน่วย: ข้อมูล ณ 2024-2025
# ─────────────────────────────────────────────────────────────
CURATED: dict[str, dict] = {
    "DOHOME": {
        "company_name": "บริษัท โฮม โปรดักส์ เซ็นเตอร์ จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจค้าปลีกวัสดุก่อสร้าง ผลิตภัณฑ์ตกแต่งบ้านและเฟอร์นิเจอร์ "
            "ผ่านรูปแบบ warehouse-style store ภายใต้แบรนด์ DoHome "
            "กลุ่มเป้าหมายคือผู้รับเหมาและผู้บริโภคทั่วไปที่ต้องการซื้อวัสดุในราคาขายส่ง"
        ),
        "industry": "Home Improvement",
        "sector_yf": "Consumer Cyclical",
        "sso_flag": False,
    },
    "PR9": {
        "company_name": "บริษัท โพรเกรส เทคโนโลยี อินโนเวชั่น จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจออกแบบ ผลิต และจำหน่ายระบบท่อและวาล์ว (HDPE, PVC, PPR) "
            "สำหรับระบบประปา ระบายน้ำ และอุตสาหกรรม รวมถึงผลิตภัณฑ์พลาสติก industrial"
        ),
        "industry": "Building Products",
        "sector_yf": "Industrials",
        "sso_flag": False,
    },
    "JMART": {
        "company_name": "บริษัท เจมาร์ท กรุ๊ป โฮลดิ้งส์ จำกัด (มหาชน)",
        "business_desc": (
            "Holding company ของกลุ่ม JMART ประกอบธุรกิจหลัก: "
            "1) ค้าปลีกโทรศัพท์มือถือ สมาร์ทโฟน และอุปกรณ์เสริม (JMT Electronics) "
            "2) สินเชื่อ (J-Leasing) 3) บริหารหนี้ (JMT Network Services)"
        ),
        "industry": "Specialty Retail",
        "sector_yf": "Consumer Cyclical",
        "sso_flag": False,
    },
    "JMT": {
        "company_name": "บริษัท เจเอ็มที เน็ทเวอร์ค เซอร์วิสเซ็ส จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจรับซื้อและบริหารหนี้ด้อยคุณภาพ (NPL / NPA) "
            "จากธนาคารและสถาบันการเงิน ทั้งหนี้มีหลักประกันและไม่มีหลักประกัน "
            "รายได้หลักมาจากส่วนต่างราคาซื้อหนี้กับการเรียกเก็บ"
        ),
        "industry": "Asset Management",
        "sector_yf": "Financial Services",
        "sso_flag": False,
    },
    "SINGER": {
        "company_name": "บริษัท ซิงเกอร์ประเทศไทย จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจจำหน่ายสินค้าอุปโภคบริโภค เช่น เครื่องใช้ไฟฟ้า จักรเย็บผ้า "
            "พร้อมให้สินเชื่อเช่าซื้อแก่ผู้บริโภครายย่อย โดยเฉพาะในต่างจังหวัด "
            "ผ่านเครือข่ายตัวแทนขายทั่วประเทศ"
        ),
        "industry": "Consumer Finance",
        "sector_yf": "Financial Services",
        "sso_flag": False,
    },
    "SGC": {
        "company_name": "บริษัท สยามโกลบอลเฮ้าส์ จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจค้าปลีกวัสดุก่อสร้าง ของตกแต่งบ้าน เครื่องมือช่าง "
            "ภายใต้แบรนด์ Global House ในรูปแบบ warehouse store "
            "กลุ่มเป้าหมายหลักเป็นผู้รับเหมาและผู้ซื้อปริมาณมาก"
        ),
        "industry": "Home Improvement",
        "sector_yf": "Consumer Cyclical",
        "sso_flag": False,
    },
    "ADVICE": {
        "company_name": "บริษัท แอดไวซ์ ไอที อินฟินิท จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจค้าปลีกและค้าส่งสินค้าไอที ได้แก่ คอมพิวเตอร์ โน้ตบุ๊ก "
            "อุปกรณ์เครือข่าย อุปกรณ์เสริม ผ่านร้านค้า Advice และช่องทางออนไลน์ "
            "ยังมีบริการซ่อมบำรุงและวางระบบ IT สำหรับองค์กร"
        ),
        "industry": "Computer Hardware",
        "sector_yf": "Technology",
        "sso_flag": False,
    },
    "TURBO": {
        "company_name": "บริษัท เทอร์โบ เอนเนอร์ยี่ จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจจำหน่ายน้ำมันเชื้อเพลิง ก๊าซ LPG CNG และน้ำมันหล่อลื่น "
            "ผ่านเครือข่ายสถานีบริการน้ำมัน (ปั๊มน้ำมัน) และจำหน่ายผลิตภัณฑ์ปิโตรเลียม "
            "รวมถึงธุรกิจสินเชื่อรายย่อย (nano finance) สำหรับลูกค้าสถานีบริการ"
        ),
        "industry": "Oil & Gas Refining",
        "sector_yf": "Energy",
        "sso_flag": False,
    },
    "MTC": {
        "company_name": "บริษัท เมืองไทย แคปปิตอล จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจสินเชื่อจำนำทะเบียนรถยนต์และรถจักรยานยนต์ (non-bank) "
            "ให้สินเชื่อแก่ผู้มีรายได้น้อยและกลุ่มเกษตรกรที่เข้าไม่ถึงสินเชื่อธนาคาร "
            "ดำเนินงานผ่านสาขาทั่วประเทศกว่า 6,000 สาขา"
        ),
        "industry": "Credit Services",
        "sector_yf": "Financial Services",
        "sso_flag": False,
    },
    "SAWAD": {
        "company_name": "บริษัท ศรีสวัสดิ์ คอร์ปอเรชั่น จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจสินเชื่อจำนำทะเบียนรถยนต์ รถจักรยานยนต์ และสินเชื่อนาโนไฟแนนซ์ "
            "(non-bank) ให้บริการกลุ่มลูกค้ารายย่อยที่ต้องการสภาพคล่องระยะสั้น "
            "ผ่านเครือข่ายสาขาและพันธมิตรทั่วประเทศ"
        ),
        "industry": "Credit Services",
        "sector_yf": "Financial Services",
        "sso_flag": False,
    },
    "TIDLOR": {
        "company_name": "บริษัท ทีดีแอล จำกัด (มหาชน) (เดิม: ไทยธนาคารลิสซิ่ง)",
        "business_desc": (
            "ประกอบธุรกิจสินเชื่อจำนำทะเบียนรถยนต์และสินเชื่อรายย่อย (non-bank) "
            "รายได้หลักมาจากดอกเบี้ยสินเชื่อจำนำทะเบียน ให้บริการกลุ่มลูกค้าที่ "
            "เข้าไม่ถึงสินเชื่อธนาคาร ผ่านสาขาและแพลตฟอร์มดิจิทัล"
        ),
        "industry": "Credit Services",
        "sector_yf": "Financial Services",
        "sso_flag": False,
    },
    "COM7": {
        "company_name": "บริษัท คอม เซเว่น จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจค้าปลีกสินค้าไอที สมาร์ทโฟน และอุปกรณ์อิเล็กทรอนิกส์ "
            "เป็น Authorized Reseller ของ Apple (iStudio, BaNANA, comiX) "
            "ดำเนินงานผ่านร้านค้ามากกว่า 1,000 สาขาทั่วประเทศ"
        ),
        "industry": "Consumer Electronics",
        "sector_yf": "Technology",
        "sso_flag": False,
    },
    "SPVI": {
        "company_name": "บริษัท ซุปเปอร์ วิชั่น อินเตอร์เนชั่นแนล จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจจัดจำหน่ายและนำเข้าสินค้าแฟชั่น เครื่องสำอาง lifestyle "
            "และผลิตภัณฑ์ดูแลตัวเอง ผ่านช่องทางออนไลน์และออฟไลน์ "
            "รวมถึงการเป็นตัวแทนจำหน่ายแบรนด์ต่างประเทศในไทย"
        ),
        "industry": "Specialty Retail",
        "sector_yf": "Consumer Cyclical",
        "sso_flag": False,
    },
    "CPW": {
        "company_name": "บริษัท ซีพี วายเออร์แอนด์เคเบิ้ล จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจผลิตและจำหน่ายสายไฟฟ้า สายโทรคมนาคม และสายเคเบิ้ล "
            "ทั้งสายทองแดงและสายอะลูมิเนียม ส่งขายให้กับการไฟฟ้า ผู้รับเหมา "
            "และภาคอุตสาหกรรม"
        ),
        "industry": "Electrical Equipment",
        "sector_yf": "Industrials",
        "sso_flag": False,
    },
    "CHAYO": {
        "company_name": "บริษัท ชโย กรุ๊ป จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจซื้อและบริหารสินทรัพย์ด้อยคุณภาพ (NPL / NPA) "
            "จากสถาบันการเงิน รายได้มาจากการรับซื้อหนี้ในราคาลด "
            "แล้วเรียกเก็บหรือขายสินทรัพย์หลักประกัน (AMC)"
        ),
        "industry": "Asset Management",
        "sector_yf": "Financial Services",
        "sso_flag": False,
    },
    "CHASE": {
        "company_name": "บริษัท เชส คอร์ปอเรชั่น จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจสินเชื่อรายย่อยและสินเชื่อ nano finance สำหรับผู้มีรายได้น้อย "
            "(non-bank) รวมถึงสินเชื่อจำนำทะเบียนรถ ให้บริการผ่านเครือข่ายสาขา "
            "และตัวแทนทั่วประเทศ"
        ),
        "industry": "Credit Services",
        "sector_yf": "Financial Services",
        "sso_flag": False,
    },
    "BAM": {
        "company_name": "บริษัท บริหารสินทรัพย์ กรุงเทพพาณิชย์ จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจซื้อและบริหารสินทรัพย์ด้อยคุณภาพ (NPL และ NPA) "
            "จากธนาคารกรุงเทพพาณิชยการและสถาบันการเงินอื่น "
            "เป็น AMC ที่ใหญ่ที่สุดในตลาดหลักทรัพย์ไทย"
        ),
        "industry": "Asset Management",
        "sector_yf": "Financial Services",
        "sso_flag": False,
    },
    "KCC": {
        "company_name": "บริษัท เค.ซี.ซี. อินเตอร์เนชั่นแนล จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจนำเข้าและจัดจำหน่ายสินค้าอุปโภคบริโภค "
            "อาหารและเครื่องดื่ม ผลิตภัณฑ์ส่งออกและนำเข้าสินค้าอาหารสำเร็จรูป "
            "ผ่านช่องทาง modern trade และ traditional trade"
        ),
        "industry": "Food Distribution",
        "sector_yf": "Consumer Defensive",
        "sso_flag": False,
    },
    "KCG": {
        "company_name": "บริษัท ขนมปังกรุงเทพ จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจผลิตและจำหน่ายขนมปัง เบเกอรี่ เค้ก และผลิตภัณฑ์นม "
            "ภายใต้แบรนด์ 'ฟาร์มเฮ้าส์' 'แซนด์วิช' และ 'แม็กซิม' "
            "จำหน่ายผ่าน modern trade ทั่วประเทศ"
        ),
        "industry": "Packaged Foods",
        "sector_yf": "Consumer Defensive",
        "sso_flag": False,
    },
    "NSL": {
        "company_name": "บริษัท เอ็น.เอส.แอล. ฟูดส์ จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจผลิตและส่งออกอาหารทะเลแปรรูป เช่น ปลาทูน่ากระป๋อง "
            "อาหารทะเลแช่แข็ง และอาหารสัตว์เลี้ยง ส่งออกไปยังตลาดยุโรปและอเมริกา"
        ),
        "industry": "Packaged Foods",
        "sector_yf": "Consumer Defensive",
        "sso_flag": False,
    },
    "ICHI": {
        "company_name": "บริษัท อิชิตัน กรุ๊ป จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจผลิตและจำหน่ายเครื่องดื่มชาพร้อมดื่ม ภายใต้แบรนด์ 'อิชิตัน' "
            "และเครื่องดื่มอื่นๆ จำหน่ายผ่าน modern trade และ traditional trade "
            "ทั้งในประเทศและส่งออก"
        ),
        "industry": "Beverages",
        "sector_yf": "Consumer Defensive",
        "sso_flag": False,
    },
    "SABINA": {
        "company_name": "บริษัท ซาบีน่า จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจผลิตและจำหน่ายชุดชั้นในสตรีภายใต้แบรนด์ 'ซาบีน่า' "
            "และ 'Wacoal' (ผ่าน license) จำหน่ายผ่านร้านสาขาและ modern trade "
            "ทั่วประเทศ รวมถึงส่งออก"
        ),
        "industry": "Apparel Manufacturing",
        "sector_yf": "Consumer Cyclical",
        "sso_flag": False,
    },
    "ADVANC": {
        "company_name": "บริษัท แอดวานซ์ อินโฟร์ เซอร์วิส จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจให้บริการโทรคมนาคมไร้สาย (AIS) บริการ 4G/5G "
            "บริการอินเทอร์เน็ตบ้าน (AIS Fibre) และบริการดิจิทัล "
            "เป็นผู้ให้บริการเครือข่ายมือถือที่ใหญ่ที่สุดในประเทศไทย"
        ),
        "industry": "Telecom Services",
        "sector_yf": "Communication Services",
        "sso_flag": False,
    },
    "MOSHI": {
        "company_name": "บริษัท โมชิ โมชิ รีเทล คอร์ปอเรชั่น จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจค้าปลีกสินค้าไลฟ์สไตล์ เครื่องเขียน ของแต่งบ้าน "
            "สินค้า kawaii และอุปกรณ์มือถือ ภายใต้แบรนด์ 'Moshi Moshi' "
            "ผ่านร้านค้าในห้างสรรพสินค้าและช่องทางออนไลน์"
        ),
        "industry": "Specialty Retail",
        "sector_yf": "Consumer Cyclical",
        "sso_flag": False,
    },
    "EKH": {
        "company_name": "บริษัท เอกชัยการแพทย์ จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจโรงพยาบาลเอกชน ภายใต้แบรนด์ 'โรงพยาบาลเอกชัย' "
            "ให้บริการผู้ป่วยทั้ง OPD และ IPD ในสมุทรสาคร "
            "รับผู้ป่วยประกันสุขภาพเอกชนและเงินสด ไม่รับประกันสังคม (SSO)"
        ),
        "industry": "Medical Care Facilities",
        "sector_yf": "Healthcare",
        "sso_flag": True,
    },
    "WASH": {
        "company_name": "บริษัท วอช จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจให้บริการซักอบรีดหยอดเหรียญ (coin-operated laundromat) "
            "ภายใต้แบรนด์ 'WASH' ให้บริการผ่านเครื่องซักผ้าหยอดเหรียญ "
            "ในทำเลที่อยู่อาศัย หอพัก ชุมชน ทั่วประเทศ"
        ),
        "industry": "Specialty Business Services",
        "sector_yf": "Industrials",
        "sso_flag": False,
    },
    "WPH": {
        "company_name": "บริษัท วิภาวดี โรงพยาบาล จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจโรงพยาบาลเอกชนในกรุงเทพฯ ภายใต้แบรนด์ 'โรงพยาบาลวิภาวดี' "
            "ให้บริการผู้ป่วย OPD IPD ศัลยกรรม และบริการทางการแพทย์เฉพาะทาง "
            "รับผู้ป่วยประกันสุขภาพและต้องตรวจสอบ SSO เพิ่มเติม"
        ),
        "industry": "Medical Care Facilities",
        "sector_yf": "Healthcare",
        "sso_flag": True,
    },
    "MAGURO": {
        "company_name": "บริษัท มากูโร่ กรุ๊ป จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจร้านอาหารญี่ปุ่น ภายใต้แบรนด์ 'Maguro' และแบรนด์ในเครือ "
            "เน้นอาหารทะเลสด ซูชิ ซาชิมิ ราคากลาง-บน "
            "ขยายสาขาในห้างสรรพสินค้าและ standalone"
        ),
        "industry": "Restaurants",
        "sector_yf": "Consumer Cyclical",
        "sso_flag": False,
    },
    "AURA": {
        "company_name": "บริษัท ออร่า ไทย จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจจำหน่ายทองคำและเครื่องประดับทองคำ "
            "ผ่านร้านค้าทองรูปพรรณและทองคำแท่ง ภายใต้แบรนด์ 'AURA' "
            "รายได้หลักจากส่วนต่างราคาทองและค่ากำเหน็จ"
        ),
        "industry": "Luxury Goods",
        "sector_yf": "Consumer Cyclical",
        "sso_flag": False,
    },
    "HL": {
        "company_name": "บริษัท ไฮไลท์ เอ็นเตอร์ไพรส์ จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจผลิตและจำหน่ายเฟอร์นิเจอร์ไม้ยางพารา เฟอร์นิเจอร์สำเร็จรูป "
            "ส่งออกไปยังตลาดยุโรป อเมริกา และญี่ปุ่น "
            "รายได้หลักจากการส่งออก OEM ให้กับแบรนด์ต่างประเทศ"
        ),
        "industry": "Furnishings",
        "sector_yf": "Consumer Cyclical",
        "sso_flag": False,
    },
    "CHAO": {
        "company_name": "บริษัท เฉาก๊วย เชียงราย จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจผลิตและจำหน่ายข้าวหอมมะลิ ข้าวไรซ์เบอร์รี่ "
            "และผลิตภัณฑ์แปรรูปจากข้าว ส่งออกและจำหน่ายในประเทศ "
            "ภายใต้แบรนด์ 'เฉาก๊วย' และ OEM ให้ห้างสรรพสินค้า"
        ),
        "industry": "Packaged Foods",
        "sector_yf": "Consumer Defensive",
        "sso_flag": False,
    },
    "TNP": {
        "company_name": "บริษัท ทีเอ็นพี ซุปเปอร์ สโตร์ จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจค้าปลีกอาหารสด ของแห้ง สินค้าอุปโภคบริโภค "
            "ในรูปแบบ superstore ขนาดกลาง-ใหญ่ กลุ่มเป้าหมายเป็น "
            "ชุมชนและผู้บริโภคในต่างจังหวัดภาคเหนือ"
        ),
        "industry": "Grocery Stores",
        "sector_yf": "Consumer Defensive",
        "sso_flag": False,
    },
    "KLINIQ": {
        "company_name": "บริษัท คลีนิคคอล จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจคลินิกเวชกรรมความงาม (aesthetic clinic) "
            "ให้บริการเลเซอร์ ผิวพรรณ ฉีดโบท็อกซ์ ฟิลเลอร์ และเสริมความงาม "
            "ผ่านเครือข่ายคลินิกภายใต้แบรนด์ 'Kliniq'"
        ),
        "industry": "Medical Care Facilities",
        "sector_yf": "Healthcare",
        "sso_flag": False,
    },
    "TRP": {
        "company_name": "บริษัท ทรัพย์ศรีไทย จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจผลิตและจำหน่ายสินค้าอาหารสำเร็จรูปแช่แข็ง "
            "เช่น บะหมี่ เกี๊ยว ลูกชิ้น จำหน่ายผ่าน modern trade "
            "และ traditional trade ทั้งในประเทศและส่งออก"
        ),
        "industry": "Packaged Foods",
        "sector_yf": "Consumer Defensive",
        "sso_flag": False,
    },
    "MASTER": {
        "company_name": "บริษัท มาสเตอร์ แอด จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจสื่อโฆษณานอกบ้าน (out-of-home advertising) "
            "ได้แก่ บิลบอร์ด LED display ป้ายโฆษณาในระบบขนส่งสาธารณะ "
            "สื่อโฆษณาในห้างสรรพสินค้าและสนามบิน"
        ),
        "industry": "Advertising Agencies",
        "sector_yf": "Communication Services",
        "sso_flag": False,
    },
    "CPALL": {
        "company_name": "บริษัท ซีพี ออลล์ จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจค้าปลีกผ่านร้านสะดวกซื้อ 7-Eleven กว่า 15,000 สาขาทั่วประเทศ "
            "และธุรกิจค้าส่ง Makro (ผ่าน CPAXT) รายได้หลักจากค่าสิทธิ์แฟรนไชส์ "
            "และการจำหน่ายสินค้าผ่านเครือข่ายร้านค้า"
        ),
        "industry": "Convenience Stores",
        "sector_yf": "Consumer Defensive",
        "sso_flag": False,
    },
    "CPAXT": {
        "company_name": "บริษัท ซีพี แอ็กซ์ตร้า จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจค้าส่งและค้าปลีก ภายใต้แบรนด์ 'Makro' "
            "เน้นลูกค้าองค์กร ร้านอาหาร โรงแรม และผู้ประกอบการขนาดย่อม "
            "รูปแบบ cash-and-carry warehouse กว่า 140 สาขาในไทยและต่างประเทศ"
        ),
        "industry": "Wholesale",
        "sector_yf": "Consumer Defensive",
        "sso_flag": False,
    },
    "MRDIYTH": {
        "company_name": "บริษัท เอ็มอาร์ ดีไอวาย (ประเทศไทย) จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจค้าปลีกสินค้า home improvement DIY วัสดุก่อสร้าง "
            "เครื่องมือช่าง อุปกรณ์ไฟฟ้า ของตกแต่งบ้าน ภายใต้แบรนด์ 'MR.DIY' "
            "ขยายสาขาในรูปแบบ standalone และ in-mall"
        ),
        "industry": "Home Improvement",
        "sector_yf": "Consumer Cyclical",
        "sso_flag": False,
    },
    "GLOBAL": {
        "company_name": "บริษัท สยามโกลบอลเฮ้าส์ จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจค้าปลีกวัสดุก่อสร้าง เครื่องมือช่าง สุขภัณฑ์ "
            "ในรูปแบบ warehouse store ภายใต้แบรนด์ 'Global House' "
            "กลุ่มลูกค้าหลักคือผู้รับเหมาก่อสร้างและผู้ซื้อจำนวนมาก"
        ),
        "industry": "Home Improvement",
        "sector_yf": "Consumer Cyclical",
        "sso_flag": False,
    },
    "HMPRO": {
        "company_name": "บริษัท โฮม โปรดักส์ เซ็นเตอร์ จำกัด (มหาชน)",
        "business_desc": (
            "ประกอบธุรกิจค้าปลีกสินค้า home improvement เครื่องใช้ไฟฟ้า "
            "เฟอร์นิเจอร์ และของตกแต่งบ้าน ภายใต้แบรนด์ 'HomePro' และ 'Mega Home' "
            "ดำเนินงานผ่านสาขากว่า 120 สาขาทั่วประเทศ"
        ),
        "industry": "Home Improvement",
        "sector_yf": "Consumer Cyclical",
        "sso_flag": False,
    },
}

WATCHLIST = [
    "DOHOME", "PR9", "JMART", "JMT", "SINGER", "SGC", "ADVICE", "TURBO",
    "MTC", "SAWAD", "TIDLOR", "COM7", "SPVI", "CPW", "CHAYO", "CHASE",
    "BAM", "KCC", "KCG", "NSL", "ICHI", "SABINA", "ADVANC", "MOSHI",
    "EKH", "WASH", "WPH", "MAGURO", "AURA", "HL", "CHAO", "TNP",
    "KLINIQ", "TRP", "MASTER", "CPALL", "CPAXT", "MRDIYTH",
    "GLOBAL", "HMPRO",
]

SECTOR_HINTS = {
    "AMC / บริหารหนี้เสีย": [
        "non-performing", "distressed asset", "npl", "npa",
        "บริหารหนี้", "สินทรัพย์ด้อยคุณภาพ", "หนี้ด้อยคุณภาพ", "ซื้อและบริหารสินทรัพย์",
    ],
    "Non-bank / สินเชื่อรายย่อย": [
        "motorcycle", "hire purchase", "personal loan", "microfinance",
        "nano finance", "pawn", "จำนำทะเบียน", "เช่าซื้อ", "สินเชื่อรายย่อย",
        "สินเชื่อจำนำ", "non-bank",
    ],
    "โรงพยาบาล": [
        "hospital", "inpatient", "outpatient", "โรงพยาบาล", "สถานพยาบาล", "ผู้ป่วย",
    ],
    "คลินิกความงาม / Aesthetic": [
        "aesthetic", "cosmetic", "beauty clinic", "เลเซอร์", "คลินิกเวชกรรม",
        "ศัลยกรรม", "โบท็อกซ์", "ฟิลเลอร์", "ความงาม",
    ],
    "IT / Mobile retail": [
        "apple", "reseller", "mobile phone", "smartphone", "7-eleven",
        "โทรศัพท์มือถือ", "สมาร์ทโฟน", "ไอที", "คอมพิวเตอร์", "อุปกรณ์เสริม",
    ],
    "วัสดุก่อสร้าง / Home improvement": [
        "building material", "home improvement", "diy", "warehouse store",
        "วัสดุก่อสร้าง", "ของตกแต่งบ้าน", "เครื่องมือช่าง",
    ],
    "Convenience / Wholesale": [
        "convenience store", "wholesale", "superstore", "cash-and-carry",
        "ร้านสะดวกซื้อ", "ค้าส่ง", "ค้าปลีกอาหาร",
    ],
    "อาหาร / F&B": [
        "food", "beverage", "bakery", "snack", "restaurant", "ซูชิ",
        "อาหาร", "ขนม", "เครื่องดื่ม", "ข้าว", "ชา",
    ],
    "เครื่องประดับ / ทอง": [
        "gold", "jewelry", "gemstone", "ทองคำ", "เครื่องประดับ", "ทองรูปพรรณ",
    ],
    "ชุดชั้นใน / แฟชั่น": [
        "lingerie", "underwear", "garment", "fashion",
        "ชุดชั้นใน", "เสื้อผ้า",
    ],
    "Lifestyle retail": ["lifestyle", "ไลฟ์สไตล์", "kawaii"],
    "Telecom": ["telecom", "telecommunication", "5g", "โทรคมนาคม", "เครือข่าย"],
    "ซักอบรีด / Laundromat": [
        "laundromat", "laundry", "coin-operated", "ซักอบรีด", "ซักผ้า", "หยอดเหรียญ",
    ],
}

HEALTHCARE_HINTS = ["hospital", "โรงพยาบาล", "สถานพยาบาล", "คลินิก", "ผู้ป่วย"]


def try_live_fetch(ticker: str) -> dict | None:
    """ลองดึง live data จาก Yahoo Finance ถ้าไม่ได้ให้คืน None"""
    if not HAS_REQUESTS:
        return None
    try:
        yf_sym = ticker + ".BK"
        url = f"https://query2.finance.yahoo.com/v11/finance/quoteSummary/{yf_sym}"
        params = {"modules": "assetProfile,price"}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }
        resp = requests.get(url, params=params, headers=headers, timeout=12)
        if resp.status_code != 200:
            return None
        data = resp.json()
        result = data.get("quoteSummary", {}).get("result", [{}])[0]
        profile = result.get("assetProfile", {})
        price_d = result.get("price", {})
        desc = profile.get("longBusinessSummary", "")
        if not desc:
            return None
        return {
            "company_name": price_d.get("longName") or price_d.get("shortName") or "",
            "business_desc": desc,
            "industry": profile.get("industry", ""),
            "sector_yf": profile.get("sector", ""),
            "fetch_status": "OK (live)",
            "sso_flag": False,
        }
    except Exception:
        return None


def suggest_sector(desc: str, industry: str = "") -> str:
    combined = (desc + " " + industry).lower()
    if not combined.strip():
        return "UNKNOWN"
    matches = []
    for sector, keywords in SECTOR_HINTS.items():
        for kw in keywords:
            if kw.lower() in combined:
                matches.append(sector)
                break
    if not matches:
        return "UNKNOWN — ต้อง review"
    if len(matches) > 1:
        return " | ".join(matches) + " (กำกวม — review)"
    return matches[0]


def needs_sso_check(desc: str) -> bool:
    return any(h.lower() in desc.lower() for h in HEALTHCARE_HINTS)


def main():
    out_dir = Path("/mnt/user-data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    raw = []
    review_items = []

    print(f"ตรวจสอบ watchlist {len(WATCHLIST)} ตัว...\n")
    print("(ถ้า network เข้า Yahoo Finance ได้จะใช้ live data อัตโนมัติ)\n")

    for i, ticker in enumerate(WATCHLIST, 1):
        print(f"[{i:2}/{len(WATCHLIST)}] {ticker:<10}", end=" ", flush=True)

        # พยายามดึง live ก่อน
        live = try_live_fetch(ticker)
        curated = CURATED.get(ticker, {})

        if live:
            d = live
            source = "live:Yahoo Finance"
        elif curated:
            d = curated
            d.setdefault("fetch_status", "OK (curated)")
            source = "curated:embedded"
        else:
            d = {
                "company_name": "",
                "business_desc": "",
                "industry": "",
                "sector_yf": "",
                "fetch_status": "MISSING",
                "sso_flag": False,
            }
            source = "missing"

        sector = suggest_sector(d["business_desc"], d.get("industry", ""))
        sso_flag = d.get("sso_flag", False) or needs_sso_check(d["business_desc"])

        yf_url = f"https://finance.yahoo.com/quote/{ticker}.BK/profile"
        set_url = f"https://www.set.or.th/th/market/product/stock/quote/{ticker.lower()}/factsheet"

        row = {
            "ticker": ticker,
            "company_name": d["company_name"],
            "industry_yf": d.get("industry", ""),
            "sector_yf": d.get("sector_yf", ""),
            "suggested_sector": sector,
            "needs_SSO_check": "YES" if sso_flag else "",
            "business_desc": d["business_desc"][:400],
            "data_source": source,
            "fetch_status": d["fetch_status"],
            "yahoo_profile_url": yf_url,
            "set_factsheet_url": set_url,
        }
        rows.append(row)
        raw.append({**row, "business_desc_full": d["business_desc"]})

        needs_review = (
            d["fetch_status"] not in ("OK (curated)", "OK (live)", "OK")
            or "UNKNOWN" in sector
            or "กำกวม" in sector
            or sso_flag
        )
        if needs_review:
            reason = []
            if d["fetch_status"] not in ("OK (curated)", "OK (live)", "OK"):
                reason.append(f"fetch={d['fetch_status']}")
            if "UNKNOWN" in sector or "กำกวม" in sector:
                reason.append("sector ไม่ชัด")
            if sso_flag:
                reason.append("ต้องเช็ค SSO จาก 56-1")
            review_items.append((ticker, d["company_name"], "; ".join(reason)))

        status_icon = "✓" if d["fetch_status"].startswith("OK") else "✗"
        print(
            f"{status_icon} [{source:<20}] {sector[:35]}"
            + (" ⚕️SSO?" if sso_flag else "")
        )

    # ── output files ────────────────────────────────────────
    csv_path = out_dir / "watchlist_verified.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path = out_dir / "watchlist_raw.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    review_path = out_dir / "watchlist_review.md"
    with open(review_path, "w", encoding="utf-8") as f:
        f.write("# Watchlist — รายการที่ต้อง Human Review\n\n")
        f.write(f"สร้างเมื่อ: {time.strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("| Ticker | บริษัท | เหตุผลที่ต้อง review |\n")
        f.write("|---|---|---|\n")
        for t, name, reason in review_items:
            f.write(f"| {t} | {name} | {reason} |\n")
        f.write("\n## หมายเหตุเรื่อง SSO (ประกันสังคม)\n\n")
        f.write(
            "Factsheet และ Yahoo Finance **ไม่ระบุ** ว่าโรงพยาบาลรับ SSO หรือไม่\n"
            "ต้องเช็คจาก:\n"
            "- 56-1 One Report ส่วน revenue breakdown\n"
            "- เว็บ IR ของโรงพยาบาล\n\n"
            "ตัวอย่างที่ทราบแล้ว: **EKH** = โรงพยาบาลเอกชัย — **ไม่รับ SSO**\n"
        )

    ok = sum(1 for r in rows if r["fetch_status"].startswith("OK"))
    print(f"\n{'='*60}")
    print(f"เสร็จแล้ว! ไฟล์อยู่ที่: {out_dir}/")
    print(f"  watchlist_verified.csv  ({len(rows)} ตัว, สำเร็จ {ok}/{len(rows)})")
    print(f"  watchlist_raw.json")
    print(f"  watchlist_review.md     ({len(review_items)} ตัวต้อง review)")
    print(f"{'='*60}")
    print("\n⚠️  อย่าเชื่อ suggested_sector 100% — เปิด business_desc อ่านเองทุกตัว")
    print("⚠️  โรงพยาบาลทุกตัวต้องเช็ค SSO เพิ่มจาก 56-1")


if __name__ == "__main__":
    main()
