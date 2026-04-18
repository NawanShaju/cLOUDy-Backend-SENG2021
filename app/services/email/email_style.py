from datetime import datetime

def generate_default_html(payload) -> str:
    """
    Generates a styled cLOUDy email when no HTML is provided.
    """
    
    body_html = payload.body.replace("\n", "<br>")

    html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background-color:#f5f7fb;font-family:Arial, Helvetica, sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td align="center">

<table width="600" cellpadding="0" cellspacing="0"
style="background:white;border-radius:8px;overflow:hidden;">

<!-- Header -->
<tr>
<td style="
background:linear-gradient(135deg,#4A90E2,#6BB6FF);
padding:24px;
color:white;
font-size:22px;
font-weight:bold;
">
☁ cLOUDy
</td>
</tr>

<!-- Body -->
<tr>
<td style="padding:16px 24px;color:#444;font-size:14px;line-height:1.6;">
{body_html}
</td>
</tr>

<!-- Footer -->
<tr>
<td style="
background:#f5f7fb;
padding:16px;
text-align:center;
font-size:12px;
color:#777;
">

This message was sent by <strong>cLOUDy</strong><br>
Cloud Order Management Platform<br>
{datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

</td>
</tr>

</table>

</td>
</tr>
</table>

</body>
</html>
"""

    return html