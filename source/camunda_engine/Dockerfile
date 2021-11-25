FROM maven:3.8.4-jdk-11
WORKDIR /app
COPY . .
RUN mvn clean package
EXPOSE 8080
ENTRYPOINT [ "java","-cp","target/lib/*","-jar","target/camunda_simulator-1.0.0-SNAPSHOT.jar" ]