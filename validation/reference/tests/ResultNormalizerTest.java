package reference;

import com.google.gson.JsonObject;
import com.google.gson.GsonBuilder;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import net.minecraft.core.RegistryAccess;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.alchemy.PotionContents;
import net.minecraft.world.item.alchemy.Potions;

public final class ResultNormalizerTest {
    public static void run(RegistryAccess registries) throws IOException {
        JsonObject compound = ResultNormalizer.item(
                PotionContents.createItemStack(Items.LINGERING_POTION, Potions.TURTLE_MASTER),
                registries);
        if (compound.getAsJsonArray("effects").size() != 2) {
            throw new AssertionError("Turtle Master must preserve both effects");
        }
        if (!compound.get("potion_id").getAsString().equals("minecraft:turtle_master")
                || !compound.getAsJsonObject("components").has("minecraft:potion_contents")) {
            throw new AssertionError("Preserve potion identifier and components: " + compound);
        }
        JsonObject slow = compound.getAsJsonArray("effects").get(0).getAsJsonObject();
        if (!slow.get("effect_id").getAsString().equals("minecraft:slowness")
                || slow.get("amplifier").getAsInt() != 3
                || slow.get("display_level").getAsInt() != 4
                || slow.get("base_duration_ticks").getAsInt() != 400
                || slow.get("base_duration_seconds").getAsDouble() != 20.0) {
            throw new AssertionError("Preserve potion base duration and amplifier: " + slow);
        }
        JsonObject resistance = compound.getAsJsonArray("effects").get(1).getAsJsonObject();
        if (!resistance.get("effect_id").getAsString().equals("minecraft:resistance")
                || resistance.get("amplifier").getAsInt() != 2
                || resistance.get("display_level").getAsInt() != 3
                || resistance.get("base_duration_ticks").getAsInt() != 400) {
            throw new AssertionError("Preserve the second compound effect: " + resistance);
        }
        JsonObject healing = ResultNormalizer.item(
                PotionContents.createItemStack(Items.LINGERING_POTION, Potions.HEALING),
                registries);
        JsonObject instant = healing.getAsJsonArray("effects").get(0).getAsJsonObject();
        if (!instant.get("instant").getAsBoolean()
                || !instant.get("effect_id").getAsString().equals("minecraft:instant_health")
                || !instant.get("base_duration_ticks").isJsonNull()
                || !instant.get("base_duration_seconds").isJsonNull()) {
            throw new AssertionError("Instant effects must not invent durations: " + instant);
        }
        JsonObject actual = new JsonObject();
        actual.add("turtle_master", compound);
        actual.add("healing", healing);
        actual.addProperty("passed", true);
        Files.writeString(Path.of("/out/normalizer-tests.json"),
                new GsonBuilder().serializeNulls().setPrettyPrinting().create().toJson(actual) + "\n");
        System.out.println("ResultNormalizerTest PASS (compound, level, base duration, instant)");
    }
}
