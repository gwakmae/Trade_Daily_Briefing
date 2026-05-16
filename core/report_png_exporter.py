# core/report_png_exporter.py
import asyncio
from playwright.async_api import async_playwright

async def html_to_png_async(
    html_content: str,
    output_path: str,
    width: int = 1920,
    height: int = 1080,
    scale: float = 2.0,  # 고화질을 위한 스케일 배수
    font_family: str = "'Malgun Gothic', 'Segoe UI', sans-serif"
) -> str:
    """
    HTML 문자열을 고화질 PNG 로 변환 (Playwright + Chromium)
    Korean font 렌더링을 위해 font_family 지정
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=scale,
        )
        page = await context.new_page()
        
        # 한글 폰트 렌더링을 위한 스타일 주입
        await page.add_style_tag(content=f"""
            * {{ font-family: {font_family} !important; }}
            body {{ -webkit-font-smoothing: antialiased; }}
        """)
        
        await page.set_content(html_content, wait_until="networkidle")
        
        # 전체 페이지 캡처 (스크롤 포함)
        await page.screenshot(
            path=output_path,
            full_page=True,
            type="png",
            # 🔥 quality=95 삭제 → PNG 는 무손실 형식이라 quality 옵션 지원 안됨
        )
        
        await browser.close()
    
    return output_path

def html_to_png(
    html_content: str,
    output_path: str,
    width: int = 1920,
    height: int = 1080,
    scale: float = 2.0
) -> str:
    """동기식 래퍼 함수"""
    return asyncio.run(
        html_to_png_async(html_content, output_path, width, height, scale)
    )