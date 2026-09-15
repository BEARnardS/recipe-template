from app.database import init_db, seed_demo_data


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    print("CookBase database initialized and demo data loaded.")
