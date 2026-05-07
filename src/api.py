from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.analytics import GraduateAnalytics

# 1. СНАЧАЛА создаём экземпляр FastAPI
app = FastAPI(title="Graduate Analytics API")

# 2. ПОТОМ создаём экземпляр аналитики
analytics = GraduateAnalytics()

# 3. ТОЛЬКО ПОТОМ используем декораторы
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/regions")
def get_regions():
    return {"regions": analytics.get_all_regions()}

@app.get("/universities")
def get_universities():
    return {"universities": analytics.get_all_universities()}

@app.get("/specialties/{university}")
def get_specialties(university: str):
    return {"specialties": analytics.get_specialties_by_university(university)}

@app.post("/top_specialties_matrix")
def top_specialties_matrix(request: dict):
    """Тепловая матрица: топ направлений в регионе по годам"""
    region = request.get('region')
    top_n = request.get('top_n', 5)
    
    result = analytics.get_top_specialties_matrix(region, top_n)
    if result.empty:
        raise HTTPException(status_code=404, detail=f"Регион '{region}' не найден")
    
    return {
        "region": region,
        "matrix": result.to_dict(orient='index'),
        "years": list(result.columns.astype(str)),
        "specialties": list(result.index)
    }

@app.post("/attractive_regions_matrix")
def attractive_regions_matrix(request: dict):
    """Тепловая матрица: топ регионов по годам"""
    university = request.get('university')
    specialty = request.get('specialty')
    top_n = request.get('top_n', 5)
    
    result = analytics.get_attractive_regions_matrix(university, specialty, top_n)
    if result.empty:
        raise HTTPException(status_code=404, detail="Нет данных")
    
    return {
        "university": university,
        "specialty": specialty,
        "matrix": result.to_dict(orient='index'),
        "years": list(result.columns.astype(str)),
        "regions": list(result.index)
    }

@app.post("/salary_forecast")
def salary_forecast(request: dict):
    """Прогноз зарплаты с историей для столбиковой диаграммы"""
    region = request.get('region')
    specialty = request.get('specialty')
    university = request.get('university')
    years_ahead = request.get('years_ahead', 3)
    
    result = analytics.get_salary_forecast(region, specialty, university, years_ahead)
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result

@app.get("/available_filters")
def get_available_filters():
    """Получить все доступные значения для фильтров"""
    return analytics.get_available_filters()