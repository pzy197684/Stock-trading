// 统一的默认值配置，消除重复的默认值设置
export const DEFAULT_CONFIG = {
  trading: {
    symbol: 'OPUSDT',
    leverage: 5,
    mode: 'dual',
    order_type: 'MARKET',
    interval: 5
  },
  parameters: {
    long: {
      first_qty: 0.01,
      add_ratio: 2.0,
      add_interval: 0.02,
      max_add_times: 3,
      tp_first_order: 0.01,
      tp_before_full: 0.015,
      tp_after_full: 0.02
    },
    short: {
      first_qty: 0.01,
      add_ratio: 2.0,
      add_interval: 0.02,
      max_add_times: 3,
      tp_first_order: 0.01,
      tp_before_full: 0.015,
      tp_after_full: 0.02
    },
    hedge: {
      trigger_loss: 0.05,
      equal_eps: 0.01,
      min_wait_seconds: 60,
      release_tp_after_full: { long: 0.02, short: 0.02 },
      release_sl_loss_ratio: { long: 1.0, short: 1.0 }
    }
  },
  safety: {
    require_manual_start: true,
    auto_stop_on_error: true,
    max_consecutive_losses: 5,
    circuit_breaker_enabled: true,
    circuit_breaker_max_drawdown: 0.08
  },
  risk_control: {
    max_daily_loss: 100.0,
    emergency_stop_loss: 0.1,
    max_total_qty: 0.5,
    tp_slippage: 0.002
  },
  execution: {
    max_slippage: 0.001,
    retry_attempts: 3,
    order_timeout: 30,
    enable_order_confirmation: true
  },
  monitoring: {
    enable_logging: true,
    enable_alerts: true,
    log_level: 'INFO'
  },
  api: {
    base_url: 'http://localhost:8001',
    timeout: 30000,
    retry_attempts: 3
  }
};

export default DEFAULT_CONFIG;