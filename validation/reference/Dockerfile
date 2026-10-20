FROM eclipse-temurin:25-jdk@sha256:2d5d5e9b533342a565907c84f47a2ec298c40cde7b13a3ca85d4950fa456a641
WORKDIR /opt/reference
COPY .cache/minecraft-26.2/server.jar server.jar
RUN echo 'cdacdfb25898de5e4b4b0e5ddcc2722f77067e46605709c2d886c000ebb63ec5  server.jar' | sha256sum -c - \
    && jar xf server.jar \
    && echo '183c0499c5f855570ee487dd38e141a53f0121f83a0b07a3bac2d8b6698823e8  META-INF/versions/26.2/server-26.2.jar' | sha256sum -c -
LABEL reference.server.sha256="cdacdfb25898de5e4b4b0e5ddcc2722f77067e46605709c2d886c000ebb63ec5"
COPY validation/reference/src src
COPY validation/reference/tests/ResultNormalizerTest.java tests/ResultNormalizerTest.java
RUN find META-INF -name '*.jar' | sort | paste -sd: > classpath \
    && javac -Xlint:all,-classfile -Werror \
        -cp "$(cat classpath)" -d classes src/reference/*.java tests/*.java \
    && printf 'Premain-Class: reference.ReferenceAgent\n' > agent.mf \
    && jar cfm agent.jar agent.mf -C classes .
COPY validation/reference/run.sh run.sh
RUN chmod +x run.sh
ENTRYPOINT ["/opt/reference/run.sh"]
