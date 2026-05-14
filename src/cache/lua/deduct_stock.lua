-- src/cache/lua/deduct_stock.lua
local keys = KEYS
local args = ARGV

-- Fase 1: Verificación (Fail-fast)
for i, key in ipairs(keys) do
    local stock = redis.call("GET", key)
    if not stock then
        return { -1, key }
    end
    if tonumber(stock) < tonumber(args[i]) then
        return { -2, key, stock }
    end
end

-- Fase 2: Deducción
for i, key in ipairs(keys) do
    redis.call("DECRBY", key, tonumber(args[i]))
end

return { 1, "OK" }
