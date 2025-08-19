import matplotlib.pyplot as plt
import io
import base64

def generate_bar_chart(df, x_col, y_col, title):
    fig, ax = plt.subplots()
    ax.bar(df[x_col], df[y_col])
    ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    plt.xticks(rotation=45)

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return {"type": "image", "image_base64": encoded}

