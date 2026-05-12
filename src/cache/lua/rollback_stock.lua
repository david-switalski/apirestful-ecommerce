-- src/cache/lua/rollback_stock.lua
local keys = KEYS
local args = ARGV

for i, key in ipairs(keys) do
    if redis.call("EXISTS", key) == 1 then
        redis.call("INCRBY", key, tonumber(args[i]))
    end
end

return { 1, "OK" }
