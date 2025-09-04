<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="UTF-8"/>
  <xsl:template match="/">
    <html>
      <head>
        <meta charset="utf-8"/>
        <title>KPIs & Risk</title>
        <style>
          body{font-family:Segoe UI,Tahoma,Arial,sans-serif;background:#f5f7fb;margin:0;padding:20px}
          .grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;max-width:1100px;margin:auto}
          .card{background:#fff;border-radius:12px;box-shadow:0 5px 14px rgba(0,0,0,.05);padding:20px}
          h2,h3{margin:0 0 10px}
          table{width:100%;border-collapse:collapse;margin-top:16px}
          th,td{padding:10px;border-bottom:1px solid #eee;text-align:left}
          th{background:#fafbff}
          .muted{color:#6c757d;font-size:12px}
        </style>
      </head>
      <body>
        <div class="grid">
          <div class="card">
            <h2>KPIs diarios</h2>
            <div class="muted">Rango: <xsl:value-of select="kpis_risk_data/time_range/start"/> — <xsl:value-of select="kpis_risk_data/time_range/end"/></div>
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Avg HR</th>
                  <th>Distancia (m)</th>
                  <th>% HR Alto</th>
                  <th>Presión Prom.</th>
                  <th>Alertas</th>
                  <th>Activo (min)</th>
                  <th>Sedentario (min)</th>
                </tr>
              </thead>
              <tbody>
                <xsl:for-each select="kpis_risk_data/kpis/item">
                  <tr>
                    <td><xsl:value-of select="timestamp"/></td>
                    <td><xsl:value-of select="average_heart_rate"/></td>
                    <td><xsl:value-of select="total_distance_traveled"/></td>
                    <td><xsl:value-of select="high_heart_rate_percentage"/></td>
                    <td><xsl:value-of select="average_arterial_pressure"/></td>
                    <td><xsl:value-of select="daily_alert_count"/></td>
                    <td><xsl:value-of select="time_active"/></td>
                    <td><xsl:value-of select="time_sedentary"/></td>
                  </tr>
                </xsl:for-each>
              </tbody>
            </table>
          </div>
          <div class="card">
            <h2>Risk Inference</h2>
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Modelo</th>
                  <th>Versión</th>
                  <th>Score</th>
                  <th>Label</th>
                </tr>
              </thead>
              <tbody>
                <xsl:for-each select="kpis_risk_data/risk/item">
                  <tr>
                    <td><xsl:value-of select="timestamp"/></td>
                    <td><xsl:value-of select="model_name"/></td>
                    <td><xsl:value-of select="model_version"/></td>
                    <td><xsl:value-of select="risk_score"/></td>
                    <td><xsl:value-of select="risk_label"/></td>
                  </tr>
                </xsl:for-each>
              </tbody>
            </table>
          </div>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
