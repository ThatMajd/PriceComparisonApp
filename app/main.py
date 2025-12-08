from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import subprocess
import os

from .database import get_db, engine, Base
from . import models, schemas

# Base.metadata.create_all(bind=engine) # Not needed as we use init.sql

app = FastAPI(title="Price Comparison API")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/vendors", response_model=List[schemas.VendorResponse])
def get_vendors(db: Session = Depends(get_db)):
    vendors = db.query(models.Vendor).order_by(models.Vendor.name).all()
    return vendors

@app.get("/products", response_model=List[schemas.ProductResponse])
def get_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).order_by(models.Product.updated_at.desc()).all()
    return products

@app.get("/scrape", response_model=List[schemas.ScrapedResult])
async def scrape(query: str, db: Session = Depends(get_db)):
    """
    Scrape product data for the given query.
    Runs multi_vendor_scrape synchronously, saves to DB, and returns results.
    """
    from multi_vendor_scrape import run_multi_vendor_scrape
    
    results = await run_multi_vendor_scrape(query, initiator="api")
    
    return [
        {"vendor": vendor_name, "product": product.__dict__}
        for vendor_name, product in results
    ]
