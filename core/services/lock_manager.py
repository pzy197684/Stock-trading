# 成对锁仓执行模块
from decimal import Decimal, getcontext
getcontext().prec = 18

from core.logger import logger
from core.managers.state_manager import StateManager
from core.services.order_service import call_place_order
from core.services.trader import get_position
from core.utils.helpers import get_equal_eps

def execute_hedge(symbol, direction, price, position, config, api_key, api_secret, order_type="MARKET", account=None):
	"""
	成对锁仓执行入口（paired lock）
	- 仅使用传入的 position 快照（不读全局 state）
	- Decimal 精算；abs(diff) <= equal_eps 时不下单但仍成对上锁
	- 对冲下单失败则不写锁仓状态（留待下一轮重试）
	"""
	try:
		sm = StateManager(account)
		platform   = config.get("platform", "CoinW")
		px         = Decimal(str(price))
		qty        = Decimal(str(position.get("qty", 0)))
		avg_price  = Decimal(str(position.get("avg_price", 0)))
		add_times  = int(position.get("add_times", 0))
		max_add    = int(config.get(direction, {}).get("max_add_times", 0))
		opp_qty    = Decimal(str(position.get("opposite_qty", 0)))
		equal_eps  = get_equal_eps(config)
		round_num  = position.get("add_times", 0)

		if px <= 0:
			logger.log_warning("⚠️ execute_hedge: 价格无效，跳过")
			return
		if qty <= 0 and opp_qty <= 0:
			logger.log_warning("⚠️ execute_hedge: 多空均无持仓，跳过（极端兜底）")
			return
		if qty <= 0 or avg_price <= 0:
			logger.log_warning(f"⚠️ execute_hedge: {direction} 无有效持仓，跳过")
			return
		if add_times < max_add:
			logger.log_warning(f"⚠️ execute_hedge: 未满仓不应触发锁仓（{add_times}/{max_add}），跳过")
			return

		logger.log_info(f"📉 锁仓触发详情 dir={direction}, qty={qty}, opp_qty={opp_qty}, avg={avg_price:.6f}, px={px:.6f}")

		diff = qty - opp_qty
		abs_diff = diff.copy_abs()
		opp_dir = "short" if direction == "long" else "long"
		placed_qty = Decimal("0")

		# === 是否需要对冲下单 ===
		if abs_diff <= equal_eps:
			logger.log_info(f"🆗 仓位已≈相等（|diff|={abs_diff} ≤ {equal_eps}），无需下对冲单")
		else:
			if diff > 0:
				side = "SELL" if opp_dir == "short" else "BUY"
				positionSide = "SHORT" if opp_dir == "short" else "LONG"
				log_dir = opp_dir
			else:
				side = "BUY" if direction == "long" else "SELL"
				positionSide = "LONG" if direction == "long" else "SHORT"
				log_dir = direction
			logger.log_info(f"🛒 对冲下单：dir={log_dir}, side={side}/{positionSide}, qty={abs_diff}")
			resp = call_place_order(
				symbol=symbol,
				side=side,
				positionSide=positionSide,
				quantity=float(abs_diff),
				order_type=order_type,
				api_key=api_key,
				api_secret=api_secret
			)
			if not isinstance(resp, dict) or "orderId" not in resp:
				logger.log_error(f"❌ 锁仓对冲下单失败：{resp}")
				return
			placed_qty = abs_diff
			logger.log_info(f"✅ 对冲下单完成，orderId={resp.get('orderId')}, qty={placed_qty}")

		locked_on_full = (add_times >= max_add)
		sm.update_state_bulk({
			"long":  {"hedge_locked": True, "hedge_stop": True, "hedge_locked_on_full": locked_on_full},
			"short": {"hedge_locked": True, "hedge_stop": True, "hedge_locked_on_full": locked_on_full}
		})
		logger.log_info("🪵 成对锁仓完成：long 与 short 均已 hedge_locked=True, hedge_stop=True")

		try:
			real_pos = get_position(api_key, api_secret, symbol) or {}
			long_q  = (real_pos.get("long")  or {}).get("qty", 0)
			long_ap = (real_pos.get("long")  or {}).get("avg_price", 0)
			short_q = (real_pos.get("short") or {}).get("qty", 0)
			short_ap= (real_pos.get("short") or {}).get("avg_price", 0)
			sm.update_state_bulk({
				"long":  {"qty": long_q,  "avg_price": long_ap,  "opposite_qty": short_q},
				"short": {"qty": short_q, "avg_price": short_ap, "opposite_qty": long_q}
			})
			logger.log_info(f"📊 对冲后持仓同步：long={long_q}@{long_ap:.4f}, short={short_q}@{short_ap:.4f}")

			equal_eps = get_equal_eps(config)
			diff = Decimal(str(long_q)) - Decimal(str(short_q))
			logger.log_info(f"📐 二次补齐判定：diff={diff}, equal_eps={equal_eps}")
			if abs(diff) > equal_eps:
				need_qty = float(abs(diff))
				if diff > 0:
					logger.log_info(f"📐 二次补齐：long-short={diff}，在 short 端补 {need_qty}")
					# 你可实现 _open_opposite_side_once 或直接补单
				else:
					logger.log_info(f"📐 二次补齐：short-long={-diff}，在 long 端补 {need_qty}")
					# 你可实现 _open_opposite_side_once 或直接补单
				# 二补后再同步一次
				real_pos2 = get_position(api_key, api_secret, symbol) or {}
				lq2  = (real_pos2.get("long")  or {}).get("qty", 0)
				la2  = (real_pos2.get("long")  or {}).get("avg_price", 0)
				sq2  = (real_pos2.get("short") or {}).get("qty", 0)
				sa2  = (real_pos2.get("short") or {}).get("avg_price", 0)
				sm.update_state_bulk({
					"long":  {"qty": lq2,  "avg_price": la2,  "opposite_qty": sq2},
					"short": {"qty": sq2, "avg_price": sa2, "opposite_qty": lq2}
				})
				logger.log_info(f"📊 二次补齐后：long={lq2}@{la2:.4f}, short={sq2}@{sa2:.4f}")
		except Exception as e:
			logger.log_warning(f"⚠️ 对冲后同步/二次补齐失败：{e}")

		import time
		try:
			hedge_wait = (config.get("hedge", {}) or {}).get("min_wait_seconds")
			if hedge_wait is not None:
				min_wait = int(hedge_wait)
				_cooldown_src = "hedge.min_wait_seconds"
			else:
				cooldown_minutes = int((config.get("risk_control", {}) or {}).get("cooldown_minutes", 1))
				min_wait = max(cooldown_minutes, 0) * 60
				_cooldown_src = "risk_control.cooldown_minutes"
		except Exception:
			min_wait = 60
			_cooldown_src = "default_60s"
		cooldown_until = int(time.time()) + max(min_wait, 0)
		sm.update_state_bulk({
			"long":  {"cooldown_until": cooldown_until},
			"short": {"cooldown_until": cooldown_until}
		})
		logger.log_info(f"⏳ 锁仓冷却开始：{min_wait}s（来源：{_cooldown_src}），至 {cooldown_until} (epoch)")

		# CSV 日志（如需可自行实现 write_log）
		# ...

	except Exception as e:
		logger.log_error(f"❌ execute_hedge 异常：{e}")
		return
