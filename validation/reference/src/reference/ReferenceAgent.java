package reference;

import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.Instrumentation;
import java.lang.classfile.ClassFile;
import java.lang.classfile.ClassTransform;
import java.lang.classfile.CodeBuilder;
import java.lang.classfile.CodeElement;
import java.lang.classfile.CodeTransform;
import java.lang.constant.ClassDesc;
import java.lang.constant.MethodTypeDesc;
import java.security.ProtectionDomain;

/** Adds a single observation callback; no RNG, loot, or effect method is transformed. */
public final class ReferenceAgent {
    private ReferenceAgent() {}

    public static void premain(String arguments, Instrumentation instrumentation) {
        instrumentation.addTransformer(new ClassFileTransformer() {
            @Override
            public byte[] transform(ClassLoader loader, String name, Class<?> redefined,
                                    ProtectionDomain domain, byte[] bytes) {
                if (!name.equals("net/minecraft/server/MinecraftServer")) {
                    return null;
                }
                CodeTransform callback = new CodeTransform() {
                    @Override
                    public void atStart(CodeBuilder builder) {
                        builder.aload(0).invokestatic(ClassDesc.of("reference.ReferenceAgent"), "onTick",
                                MethodTypeDesc.ofDescriptor("(Ljava/lang/Object;)V"));
                    }

                    @Override
                    public void accept(CodeBuilder builder, CodeElement element) {
                        builder.with(element);
                    }
                };
                return ClassFile.of().transformClass(ClassFile.of().parse(bytes),
                        ClassTransform.transformingMethodBodies(
                                method -> method.methodName().equalsString("tickServer")
                                        && method.methodType().equalsString("(Ljava/util/function/BooleanSupplier;)V"),
                                callback));
            }
        });
    }

    public static void onTick(Object server) {
        ReferenceQuery.onTick((net.minecraft.server.MinecraftServer) server);
    }
}
