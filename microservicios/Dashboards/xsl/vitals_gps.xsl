<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" doctype-public="-//W3C//DTD HTML 4.01 Transitional//EN" encoding="UTF-8"/>
  <xsl:template match="/">
    <html>
      <head>
        <meta charset="utf-8"/>
        <title>Vitals & GPS</title>
        <style>
          body{font-family:Segoe UI,Tahoma,Arial,sans-serif;background:#f5f7fb;margin:0;padding:20px}
          .card{background:#fff;border-radius:12px;box-shadow:0 5px 14px rgba(0,0,0,.05);padding:20px;margin:auto;max-width:1100px}
          h2{margin:0 0 10px}
          .muted{color:#6c757d;font-size:12px}
          table{width:100%;border-collapse:collapse;margin-top:16px}
          th,td{padding:10px;border-bottom:1px solid #eee;text-align:left}
          th{background:#fafbff}
          .tag{display:inline-block;padding:2px 8px;border-radius:10px;background:#eef2ff;color:#4338ca;font-size:12px}
        </style>
      </head>
      <body>
        <div class="card">
          <h2>Vitals & GPS <span class="tag">Últimas 24h</span></h2>
          <div class="muted">
            Rango: <xsl:value-of select="vitals_gps_data/time_range/start"/> — <xsl:value-of select="vitals_gps_data/time_range/end"/>
          </div>
          <h3>Vitals</h3>
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>HR</th>
                <th>Sys BP</th>
                <th>Dia BP</th>
              </tr>
            </thead>
            <tbody>
              <xsl:for-each select="vitals_gps_data/vitals/item">
                <tr>
                  <td><xsl:value-of select="timestamp"/></td>
                  <td><xsl:value-of select="heart_rate"/></td>
                  <td><xsl:value-of select="systolic_bp"/></td>
                  <td><xsl:value-of select="diastolic_bp"/></td>
                </tr>
              </xsl:for-each>
            </tbody>
          </table>
          <h3 style="margin-top:24px">GPS</h3>
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Lat</th>
                <th>Lon</th>
              </tr>
            </thead>
            <tbody>
              <xsl:for-each select="vitals_gps_data/gps/item">
                <tr>
                  <td><xsl:value-of select="timestamp"/></td>
                  <td><xsl:value-of select="lat"/></td>
                  <td><xsl:value-of select="lon"/></td>
                </tr>
              </xsl:for-each>
            </tbody>
          </table>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
