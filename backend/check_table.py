from sqlalchemy import create_engine, text
engine = create_engine('sqlite:///./cognitive.db')
with engine.connect() as conn:
    result = conn.execute(text("PRAGMA table_info(assessment_results)"))
    for row in result:
        print(row)