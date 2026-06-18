# points_manager.py
from database import Database
from config import TOOL_COST

db = Database()

class PointsManager:
    @staticmethod
    def get_points(user_id):
        return db.get_points(user_id)

    @staticmethod
    def can_use_tool(user_id):
        return db.is_premium(user_id) or db.get_points(user_id) >= TOOL_COST

    @staticmethod
    def use_tool(user_id):
        if db.is_premium(user_id):
            return True
        return db.deduct_points(user_id, TOOL_COST)

    @staticmethod
    def add_points(user_id, amount):
        db.add_points(user_id, amount)