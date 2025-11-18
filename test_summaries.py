import pandas as pd
from bin.analysis.summaries import group_by_space

def test_group_by_space_basic():
    df = pd.DataFrame({
        "region": ["A", "A", "A", "B", "B"],
        "category": ["x", "x", "y", "y", "z"]
    })

    data_path = "/Users/work/Documents/Programming/test/ITA_TEST/output/firms_data.csv"
    df = pd.read_csv(data_path)

    out = group_by_space(df, "nuts1", ["woco"])

    print(out)

    # assert isinstance(out, str)
    # assert "Interpret top categories per spatial unit." in out
# 
    # # A: x=2, y=1
    # assert "A" in out
    # assert "x" in out
    # assert "2" in out  # count of x in region A
# 
    # # B: y=1, z=1
    # assert "B" in out
    # assert "z" in out
    # assert "1" in out  # counts appear in the table


if __name__ == "__main__":
    test_group_by_space_basic()