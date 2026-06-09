

# --- DELETE OPEX endpoint — append to dashboard_routes.py ---
@router.delete("/opex/{opex_id}")
async def dashboard_delete_opex(opex_id: int, user: dict = Depends(get_current_user)):
    """Delete an OPEX expense by ID. Only the recording user or an admin can delete."""
    try:
        expense = _mysql_query_one("SELECT id, recorded_by FROM opex WHERE id = %s", (opex_id,))
        if not expense:
            return {"success": False, "error": "Expense not found"}
        
        # Only the user who recorded it or an admin can delete
        if user.get("role") != "admin" and user.get("username") != (expense.get("recorded_by") or ""):
            return {"success": False, "error": "Not authorized to delete this expense"}
        
        _mysql_delete("DELETE FROM opex WHERE id = %s", (opex_id,))
        return {"success": True, "message": "Expense deleted"}
    except Exception as e:
        logger.error(f"DELETE /opex/{opex_id} error: {e}")
        return {"success": False, "error": str(e)}
