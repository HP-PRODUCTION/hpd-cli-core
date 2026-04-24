import os
import subprocess
import json
from datetime import datetime
from sqlalchemy import text
from hpd_cli.config import ensure_config
from hpd_cli import logger

def setup_parser(subparsers):
    parser = subparsers.add_parser("etl", help="Comandos de ETL y Observabilidad")
    etl_subparsers = parser.add_subparsers(dest="etl_command", help="Subcomandos de ETL")
    etl_subparsers.required = True
    
    # 1. RUN
    run_parser = etl_subparsers.add_parser("run", help="Ejecutar un pipeline")
    run_parser.add_argument("pipeline", help="Nombre del pipeline a ejecutar")
    
    # 2. QUALITY
    quality_parser = etl_subparsers.add_parser("quality", help="Consultar calidad de datos")
    quality_parser.add_argument("--pipeline", help="Filtrar por pipeline")
    quality_parser.add_argument("--threshold", type=float, default=5.0, help="Umbral de alerta (%)")
    
    # 3. REJECTIONS
    rejections_parser = etl_subparsers.add_parser("rejections", help="Ver registros rechazados")
    rejections_parser.add_argument("--pipeline", help="Filtrar por pipeline")
    rejections_parser.add_argument("--limit", type=int, default=5, help="Número de registros a mostrar")

    # 4. HEALTH
    health_parser = etl_subparsers.add_parser("health", help="Estado general de salud del ETL")

    # 5. METRICS
    metrics_parser = etl_subparsers.add_parser("metrics", help="Métricas detalladas de rendimiento")
    metrics_parser.add_argument("--pipeline", help="Filtrar por pipeline")

    # 6. AIRFLOW
    airflow_parser = etl_subparsers.add_parser("airflow", help="Estado de la orquestación (Airflow)")
    af_sub = airflow_parser.add_subparsers(dest="airflow_command", help="Comandos de Airflow")
    af_sub.add_parser("status", help="Ver estado de contenedores Airflow")
    
    # 7. WATERMARKS
    wm_parser = etl_subparsers.add_parser("watermarks", help="Gestión de puntos de sincronización")
    wm_sub = wm_parser.add_subparsers(dest="wm_command", help="Subcomandos de watermarks")
    wm_sub.add_parser("show", help="Mostrar watermarks actuales")
    reset_parser = wm_sub.add_parser("reset", help="Resetear un watermark")
    reset_parser.add_argument("pipeline", help="Nombre del pipeline")
    reset_parser.add_argument("--to", required=True, help="Nueva fecha (YYYY-MM-DD)")

    # 8. DOCTOR
    doctor_parser = etl_subparsers.add_parser("doctor", help="Diagnóstico completo del sistema")
    doctor_parser.add_argument("--compact", action="store_true", help="Salida resumida de una línea")
    doctor_parser.add_argument("--json", action="store_true", help="Salida en formato JSON para CI/CD")
    doctor_parser.add_argument("--history", action="store_true", help="Ver tendencia de salud de los últimos días")
    doctor_parser.add_argument("--days", type=int, default=7, help="Días para evaluar calidad")

    parser.set_defaults(func=execute)

def _get_db_conn():
    try:
        from etl.config.db import get_engine
        return get_engine().connect()
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return None

def execute(args):
    config = ensure_config()
    
    if args.etl_command == "run":
        logger.info(f"HPD ETL Engine: Ejecutando pipeline '{args.pipeline}'...")
        script_path = os.path.join(config["directories"]["etl"], "pipelines", f"{args.pipeline}.py")
        if os.path.exists(script_path):
            env = os.environ.copy()
            subprocess.run(["python3", "-m", f"etl.pipelines.{args.pipeline}"], env=env)
        else:
            logger.warning(f"No se encontro el script de ETL {script_path}.")

    elif args.etl_command == "quality":
        conn = _get_db_conn()
        if not conn: return
        
        query = "SELECT * FROM analytics.vw_quality_audit"
        params = {}
        if args.pipeline:
            query += " WHERE pipeline_name = :p"
            params["p"] = args.pipeline
        query += " LIMIT 10"
        
        results = conn.execute(text(query), params).mappings().all()
        
        print("\n📊 REPORTE DE CALIDAD (Últimas ejecuciones)")
        print("-" * 100)
        print(f"{'PIPELINE':<15} | {'INICIO':<20} | {'STATUS':<8} | {'EXT':<6} | {'REJ':<6} | {'RATE':<6}% | {'MOTIVOS'}")
        print("-" * 100)
        
        for r in results:
            rate = float(r["rejection_rate"])
            color = "🔴" if rate > args.threshold else "🟢"
            status_color = "✅" if r["status"] == "SUCCESS" else "❌"
            
            print(f"{r['pipeline_name']:<15} | {str(r['started_at'])[:19]:<20} | {status_color} {r['status']:<6} | {r['rows_extracted']:<6} | {r['rows_rejected']:<6} | {color} {rate:<5.1f} | {r['reasons_summary']}")
        print("-" * 100)

    elif args.etl_command == "rejections":
        conn = _get_db_conn()
        if not conn: return
        
        query = "SELECT * FROM analytics.pipeline_rejections"
        params = {}
        if args.pipeline:
            query += " WHERE pipeline_name = :p"
            params["p"] = args.pipeline
        query += " ORDER BY rejected_at DESC LIMIT :l"
        params["l"] = args.limit
        
        results = conn.execute(text(query), params).mappings().all()
        
        print(f"\n🗑️ ÚLTIMOS {args.limit} RECHAZOS")
        print("-" * 100)
        for r in results:
            print(f"[{r['rejected_at']}] Pipeline: {r['pipeline_name']} | Motivo: {r['reason']}")
            print(f"Record: {r['record']}")
            print("-" * 50)

    elif args.etl_command == "health":
        conn = _get_db_conn()
        if not conn: return
        
        # Consultar salud general (watermarks vs fecha actual)
        query = """
            SELECT 
                pipeline_name, 
                last_value, 
                EXTRACT(EPOCH FROM (now() - last_value))/3600 as hours_since_last_sync
            FROM analytics.etl_watermarks
        """
        results = conn.execute(text(query)).mappings().all()
        
        print("\n🏥 ESTADO DE SALUD DEL ETL")
        print("-" * 60)
        print(f"{'PIPELINE':<20} | {'ÚLTIMA SINCRONIZACIÓN':<25} | {'STALE (H)'}")
        print("-" * 60)
        for r in results:
            stale = float(r["hours_since_last_sync"])
            status = "🚨" if stale > 24 else "🍏"
            print(f"{status} {r['pipeline_name']:<18} | {str(r['last_value']):<25} | {stale:.1f}")
        print("-" * 60)

    elif args.etl_command == "metrics":
        conn = _get_db_conn()
        if not conn: return
        
        query = """
            SELECT 
                pipeline_name,
                AVG(duration_ms) as avg_duration,
                SUM(rows_loaded) as total_loaded,
                MAX(duration_ms) as max_duration,
                COUNT(*) as runs
            FROM analytics.pipeline_metrics
            WHERE started_at > now() - interval '7 days'
        """
        if args.pipeline:
            query += " AND pipeline_name = :p"
        query += " GROUP BY 1"
        
        results = conn.execute(text(query), {"p": args.pipeline} if args.pipeline else {}).mappings().all()
        
        print("\n📈 MÉTRICAS DE RENDIMIENTO (Últimos 7 días)")
        print("-" * 80)
        print(f"{'PIPELINE':<20} | {'RUNS':<6} | {'AVG DUR (ms)':<15} | {'MAX DUR (ms)':<15} | {'TOTAL ROWS'}")
        print("-" * 80)
        for r in results:
            print(f"{r['pipeline_name']:<20} | {r['runs']:<6} | {int(r['avg_duration']):<15} | {r['max_duration']:<15} | {r['total_loaded']}")
        print("-" * 80)

    elif args.etl_command == "airflow":
        # Por defecto mostramos status si no hay comando específico
        cmd = args.airflow_command if hasattr(args, 'airflow_command') and args.airflow_command else "status"
        
        if cmd == "status":
            print("\n☁️ ESTADO DE ORQUESTACIÓN (Airflow Containers)")
            print("-" * 80)
            try:
                result = subprocess.run(
                    ["docker", "ps", "--filter", "name=airflow", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
                    capture_output=True, text=True
                )
                print(result.stdout)
            except Exception as e:
                logger.error(f"Error consultando Docker: {e}")
            print("-" * 80)

    elif args.etl_command == "watermarks":
        conn = _get_db_conn()
        if not conn: return
        
        if args.wm_command == "show":
            results = conn.execute(text("SELECT * FROM analytics.etl_watermarks ORDER BY pipeline_name")).mappings().all()
            print("\n📌 PUNTOS DE SINCRONIZACIÓN (Watermarks)")
            print("-" * 60)
            print(f"{'PIPELINE':<25} | {'ÚLTIMO VALOR'}")
            print("-" * 60)
            for r in results:
                print(f"{r['pipeline_name']:<25} | {r['last_value']}")
            print("-" * 60)
        
        elif args.wm_command == "reset":
            try:
                conn.execute(
                    text("UPDATE analytics.etl_watermarks SET last_value = :v WHERE pipeline_name = :p"),
                    {"v": args.to, "p": args.pipeline}
                )
                conn.commit()
                logger.success(f"Watermark de '{args.pipeline}' reseteado a {args.to}")
            except Exception as e:
                logger.error(f"Error reseteando watermark: {e}")

    elif args.etl_command == "doctor":
        conn = _get_db_conn()
        if args.history:
            if not conn: return
            results = conn.execute(text("SELECT timestamp, overall_status FROM analytics.doctor_log ORDER BY timestamp DESC LIMIT 10")).mappings().all()
            print("\n📈 TENDENCIA DE SALUD (Historial Doctor)")
            print("-" * 50)
            print(f"{'FECHA Y HORA':<20} | {'ESTADO'}")
            print("-" * 50)
            for r in results:
                icon = "🟢" if r["overall_status"] == "OK" else ("🟡" if r["overall_status"] == "WARN" else "🔴")
                print(f"{r['timestamp'].strftime('%Y-%m-%d %H:%M'):<20} | {icon} {r['overall_status']}")
            print("-" * 50)
            return

        checks = []
        
        # 1. DB Connectivity
        db_status = {"name": "Postgres connectivity", "status": "OK", "detail": "localhost:5433 / etl_db"}
        if not conn:
            db_status["status"] = "FAIL"
            db_status["detail"] = "Connection refused"
        checks.append(db_status)

        if conn:
            # 2. Alembic
            try:
                ver = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
                checks.append({"name": "Alembic migration head", "status": "OK", "detail": f"{ver} (head)"})
            except:
                checks.append({"name": "Alembic migration head", "status": "WARN", "detail": "alembic_version table missing"})

            # 3. Core Tables
            try:
                tables = conn.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'analytics' AND table_name IN ('fact_indicadores', 'pipeline_metrics', 'pipeline_rejections')")).scalar()
                checks.append({"name": "Core tables", "status": "OK" if tables >= 3 else "WARN", "detail": "fact_indicadores, metrics, rejections"})
            except:
                checks.append({"name": "Core tables", "status": "FAIL", "detail": "Analytics schema inaccessible"})

        # 4. Airflow
        try:
            ps = subprocess.run(["docker", "ps", "--filter", "name=airflow", "--format", "{{.Names}}"], capture_output=True, text=True).stdout
            sched = "airflow_scheduler" in ps
            web = "airflow_webserver" in ps
            checks.append({"name": "Airflow scheduler", "status": "OK" if sched else "FAIL", "detail": "running" if sched else "stopped"})
            checks.append({"name": "Airflow webserver", "status": "OK" if web else "FAIL", "detail": "http://localhost:8080" if web else "stopped"})
        except:
            checks.append({"name": "Airflow", "status": "FAIL", "detail": "Docker daemon unreachable"})

        # 5. Data Freshness & Quality
        if conn:
            try:
                stale = conn.execute(text("SELECT EXTRACT(EPOCH FROM (now() - MAX(last_value)))/3600 FROM analytics.etl_watermarks")).scalar()
                last_run = conn.execute(text("SELECT status, rows_extracted, finished_at FROM analytics.pipeline_metrics ORDER BY finished_at DESC LIMIT 1")).mappings().first()
                
                fresh_status = "OK"
                fresh_detail = f"{int(stale)}h stale" if stale else "No data"
                
                if stale and stale > 24:
                    # Check if it's expected inactivity (Last run was SUCCESS but 0 rows extracted)
                    if last_run and last_run["status"] == "SUCCESS" and (last_run["rows_extracted"] == 0 or last_run["rows_extracted"] is None):
                        fresh_status = "WARN"
                        fresh_detail = f"{int(stale)}h stale (source inactivity expected)"
                    else:
                        fresh_status = "FAIL" if stale > 48 else "WARN"
                
                checks.append({"name": "Data freshness", "status": fresh_status, "detail": fresh_detail})
                
                qual = conn.execute(text("SELECT rejection_rate FROM analytics.vw_quality_audit LIMIT 1")).scalar()
                q_status = "OK"
                if qual and float(qual) > 5.0: q_status = "FAIL"
                elif qual and float(qual) > 1.0: q_status = "WARN"
                checks.append({"name": "Rejection rate", "status": q_status, "detail": f"{float(qual or 0):.1f}% últimos 7 días"})
            except:
                checks.append({"name": "Data Health", "status": "WARN", "detail": "Metrics/Watermarks view missing"})

            # 6. RLS
            try:
                rls = conn.execute(text("SELECT count(*) FROM pg_policies WHERE schemaname = 'analytics'")).scalar()
                checks.append({"name": "RLS policies", "status": "OK" if rls > 0 else "WARN", "detail": f"enabled + {rls} policies"})
            except: pass

        # Persist results
        overall = "OK"
        if any(c["status"] == "FAIL" for c in checks): overall = "FAIL"
        elif any(c["status"] == "WARN" for c in checks): overall = "WARN"
        
        if conn:
            try:
                import json as json_lib
                conn.execute(
                    text("INSERT INTO analytics.doctor_log (overall_status, checks_json) VALUES (:s, :j)"),
                    {"s": overall, "j": json_lib.dumps(checks)}
                )
                conn.commit()
            except: pass

        # OUTPUT RENDERING
        if args.json:
            import json
            print(json.dumps({"project": "proyecto_anaconda", "timestamp": str(datetime.now()), "checks": checks}, indent=2))
        elif args.compact:
            status_map = {"OK": "🟢", "WARN": "🟡", "FAIL": "🔴"}
            summary = " | ".join([f"{c['name']}: {status_map[c['status']]}" for c in checks if c['status'] != "OK"])
            if not summary: summary = "🟢 Todo OK"
            print(f"🐍 Anaconda Doctor: {summary}")
        else:
            print(f"\n🐍 HPD Anaconda Doctor")
            print(f"Proyecto: proyecto_anaconda | Timestamp: {str(datetime.now())[:19]}")
            print("-" * 100)
            print(f"{'Check':<30} | {'Estado':<8} | {'Detalle'}")
            print("-" * 100)
            for c in checks:
                icon = "🟢 OK" if c["status"] == "OK" else ("🟡 WARN" if c["status"] == "WARN" else "🔴 FAIL")
                print(f"{c['name']:<30} | {icon:<8} | {c['detail']}")
            print("-" * 100)
            
            fails = [c for c in checks if c["status"] in ("FAIL", "WARN")]
            if not fails:
                print("✅ Sistema saludable. Acción requerida: ninguna.\n")
            else:
                print("🟡 Sistema operativo con advertencias/fallos. Revisar 'Detalle'.\n")
