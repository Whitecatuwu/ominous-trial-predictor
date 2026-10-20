package reference;

import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.nio.file.Files;
import java.nio.file.Path;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.block.entity.trialspawner.TrialSpawnerConfig;
import net.minecraft.world.level.block.entity.trialspawner.TrialSpawnerStateData;

public final class ReferenceQuery {
    private static boolean completed;

    private ReferenceQuery() {}

    public static void onTick(MinecraftServer server) {
        if (completed) {
            return;
        }
        completed = true;
        try {
            JsonObject request = JsonParser.parseString(Files.readString(Path.of("/request.json"))).getAsJsonObject();
            if (request.get("normalizer_tests").getAsBoolean()) {
                ResultNormalizerTest.run(server.registryAccess());
            }
            var level = server.overworld();
            long seed = Long.parseLong(request.get("seed").getAsString());
            if (level.getSeed() != seed || !server.getServerVersion().equals("26.2")) {
                throw new IllegalStateException("Unexpected server version or world seed");
            }
            var configKey = ResourceKey.create(Registries.TRIAL_SPAWNER_CONFIG,
                    Identifier.parse("minecraft:trial_chamber/melee/zombie/ominous"));
            TrialSpawnerConfig config = server.registryAccess().lookupOrThrow(Registries.TRIAL_SPAWNER_CONFIG)
                    .getValueOrThrow(configKey);
            var method = TrialSpawnerStateData.class.getDeclaredMethod(
                    "lowResolutionPosition", net.minecraft.server.level.ServerLevel.class, BlockPos.class);
            method.setAccessible(true);
            JsonObject document = new JsonObject();
            document.addProperty("game_version", "26.2");
            document.addProperty("version_status", "unverified");
            document.addProperty("seed", Long.toString(seed));
            document.addProperty("reference_method", "TrialSpawnerStateData.getDispensingItems");
            JsonObject state = new JsonObject();
            state.addProperty("dimension", "minecraft:overworld");
            state.addProperty("world", "fresh_default_world_per_invocation");
            state.addProperty("spawner_cache", "new_TrialSpawnerStateData_per_position");
            state.addProperty("config", configKey.identifier().toString());
            state.addProperty("loot_table", config.itemsToDropWhenOminous().identifier().toString());
            state.addProperty("data_packs", "vanilla_only");
            JsonArray packs = new JsonArray();
            for (String pack : server.getPackRepository().getSelectedIds()) {
                if (!pack.equals("vanilla")) {
                    throw new IllegalStateException("Unexpected data pack: " + pack);
                }
                packs.add(pack);
            }
            state.add("selected_packs", packs);
            state.addProperty("scope", "dispensing_candidates_and_weights_not_timed_entity_selection");
            document.add("world_state", state);
            JsonArray rows = new JsonArray();
            for (var input : request.getAsJsonArray("positions")) {
                var coordinates = input.getAsJsonArray();
                BlockPos position = new BlockPos(coordinates.get(0).getAsInt(),
                        coordinates.get(1).getAsInt(), coordinates.get(2).getAsInt());
                JsonObject row = new JsonObject();
                JsonObject xyz = new JsonObject();
                xyz.addProperty("x", position.getX());
                xyz.addProperty("y", position.getY());
                xyz.addProperty("z", position.getZ());
                row.add("position", xyz);
                long mixedSeed = (long) method.invoke(null, level, position);
                row.addProperty("mixed_seed", Long.toString(mixedSeed));
                if (mixedSeed == 0) {
                    row.addProperty("status", "requires_world_state");
                    row.addProperty("reason", "zero_mixed_seed_uses_world_random_sequence_state");
                    row.add("result", JsonNull.INSTANCE);
                } else {
                    var items = new TrialSpawnerStateData().getDispensingItems(level, config, position);
                    JsonArray results = new JsonArray();
                    for (var weighted : items.unwrap()) {
                        JsonObject item = ResultNormalizer.item(weighted.value(), server.registryAccess());
                        item.addProperty("weight", weighted.weight());
                        results.add(item);
                    }
                    JsonObject result = new JsonObject();
                    result.add("dispensing_items", results);
                    row.addProperty("status", "ok");
                    row.add("result", result);
                }
                rows.add(row);
            }
            document.add("rows", rows);
            Files.copy(Path.of("server.properties"), Path.of("/out/server.properties"));
            Files.writeString(Path.of("/out/result.json"), new GsonBuilder().serializeNulls()
                    .setPrettyPrinting().create().toJson(document) + "\n");
        } catch (Throwable error) {
            error.printStackTrace();
        } finally {
            server.halt(false);
        }
    }
}
