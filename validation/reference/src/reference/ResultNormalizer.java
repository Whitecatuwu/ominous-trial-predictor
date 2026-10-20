package reference;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.mojang.serialization.JsonOps;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.component.DataComponentMap;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.alchemy.PotionContents;

/** Serializes original registry/ItemStack data; does not calculate loot or RNG. */
public final class ResultNormalizer {
    private ResultNormalizer() {}

    public static JsonObject item(ItemStack stack, RegistryAccess registries) {
        JsonObject result = new JsonObject();
        result.addProperty("item_id", BuiltInRegistries.ITEM.getKey(stack.getItem()).toString());
        result.addProperty("count", stack.getCount());
        result.add("components", DataComponentMap.CODEC.encodeStart(
                registries.createSerializationContext(JsonOps.INSTANCE), stack.getComponents()).getOrThrow());
        PotionContents contents = stack.get(DataComponents.POTION_CONTENTS);
        String potionId = contents == null ? null : contents.potion()
                .map(holder -> holder.unwrapKey().orElseThrow().identifier().toString()).orElse(null);
        result.addProperty("potion_id", potionId);
        JsonArray effects = new JsonArray();
        if (contents != null) {
            for (var effect : contents.getAllEffects()) {
                JsonObject entry = new JsonObject();
                entry.addProperty("effect_id", effect.getEffect().unwrapKey().orElseThrow().identifier().toString());
                entry.addProperty("amplifier", effect.getAmplifier());
                entry.addProperty("display_level", effect.getAmplifier() + 1);
                boolean instant = effect.getEffect().value().isInstantaneous();
                entry.addProperty("instant", instant);
                // Preserve the raw registry value even when it is only an instant-effect sentinel.
                entry.addProperty("raw_duration_ticks", effect.getDuration());
                if (instant || effect.isInfiniteDuration()) {
                    entry.add("base_duration_ticks", JsonNull.INSTANCE);
                    entry.add("base_duration_seconds", JsonNull.INSTANCE);
                } else {
                    entry.addProperty("base_duration_ticks", effect.getDuration());
                    entry.addProperty("base_duration_seconds", effect.getDuration() / 20.0);
                }
                entry.addProperty("infinite", effect.isInfiniteDuration());
                effects.add(entry);
            }
        }
        result.add("effects", effects);
        return result;
    }
}
