from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.api.auth import get_current_admin
from app.services.excel_sync import regenerate_excel, get_export_path
import os

router = APIRouter()


@router.get("/excel")
def download_excel(_=Depends(get_current_admin)):
    path = get_export_path()
    # Regenerate fresh file on every download request
    try:
        regenerate_excel()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Excel: {str(e)}")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Export file not found")

    return FileResponse(
        path=path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"lottery_users_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
    )
