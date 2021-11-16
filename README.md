Human BPI with Reinforcement Learning project as part of module "(Advanced) Distributed Systems Prototyping" at TU Berlin. 2021/2022

Entry here:
_org/example/sbe_prototyping/WebappExampleProcessApplication.java_

Run main() and observe the tasklist and Cockpit at http://localhost:8080/ with your browser

The operation
`runtimeService.startProcessInstanceByKey("food");`
loads a bpmn file from the _src/main/resources_ dir, drag it to the Modeler to have a better view~

# Detailed tutorial
##Create the Camunda Spring Boot project
Create an empty Maven project named sbe_prototyping and groupId org.example

##Configuring Maven dependencies
Next add the Maven dependency, which needs to be added to the `pom.xml` file in the project root directory.  We need to add the Spring Boot dependency to "Dependency Management", and then add Camunda Spring Boot Starter as a dependency, which will provide the Camunda process engine and its own WebApp;  For simplicity, the database uses an embedded H2 database;  Finally, add `spring-boot-Maven-plugin`, which packages spring Boot projects together.  The final result is as follows:  
```<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
<modelVersion>4.0.0</modelVersion>

    <groupId>org.example</groupId>
    <artifactId>sbe_prototyping</artifactId>
    <version>1.0-SNAPSHOT</version>

    <properties>
        <camunda.spring-boot.version>7.15.0</camunda.spring-boot.version>
        <spring-boot.version>2.4.4</spring-boot.version>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>

    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-dependencies</artifactId>
                <version>${spring-boot.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>

    <dependencies>
        <dependency>
            <groupId>org.camunda.bpm.springboot</groupId>
            <artifactId>camunda-bpm-spring-boot-starter-webapp</artifactId>
            <version>${camunda.spring-boot.version}</version>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
        </dependency>
        <dependency>
            <groupId>com.sun.xml.bind</groupId>
            <artifactId>jaxb-impl</artifactId>
            <version>2.2.3</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <version>${spring-boot.version}</version>
                <configuration>
                    <layout>ZIP</layout>
                </configuration>
                <executions>
                    <execution>
                        <goals>
                            <goal>repackage</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

##Add the main class for the project
Next, we'll add a main class for the application to run. Create the class under `src/main/java` named `WebappExampleProcessApplication`
The main class of SpringBoot needs to add the @SpringBootApplication annotation. The resulting effect is as follows:
```package org.example.loanapproval;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class WebappExampleProcessApplication {

    public static void main(String... args) {
        SpringApplication.run(WebappExampleProcessApplication.class, args);
    }
}
```

## Configuration items

Camunda Spring Boot comes with best practice configurations that are automatically enabled at startup. To override some of these configurations, add `application.yaml` or `application.properties` to resources.  The specific content of the default configuration can check https://docs.camunda.org/manual

## User-defined administrator accounts

Let's create the `application.yaml` file under `src/main/resources` and type the following:  
```camunda.bpm:
admin-user:
id: demo
password: demo
firstName: Demo
filter:
create: All tasks
```
The preceding configuration uses Demo as the administrator user name and password, and adds the All Tasks filter to the Tasklist

## Compile operation

IDEs usually have tools that can be compiled and run directly

You can also run it from the command line:

`mvn package ` 
`Java - jar target/***.jar`

Open the browser to http://localhost:8080/, and the login screen will be automatically opened. You can log in to demo/ Demo and open Tasklist. You can see that "All Tasks" is also created.

## Enable process support for projects

Now we add the `@EnableProcessApplication` annotation to the Camunda Spring Boot project, which provides more configurable items and enables more process-related annotations.  
```
package org.example.loanapproval;

import org.camunda.bpm.spring.boot.starter.annotation.EnableProcessApplication;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@EnableProcessApplication // new
public class WebappExampleProcessApplication {

    public static void main(String... args) {
        SpringApplication.run(WebappExampleProcessApplication.class, args);
    }
}
```

## Initiate process tests during process deployment

The next step is a test where we want to initiate a process after the process is deployed using the EventListener annotation `@Eventlistener` of type `PostDeployEvent`,  The modified `WebappExampleProcessApplication` is as follows:  

```
@SpringBootApplication
@EnableProcessApplication
public class WebappExampleProcessApplication {

    public static void main(String... args) {
        SpringApplication.run(WebappExampleProcessApplication.class, args);
    }

    // >>new
    @Autowired
    private RuntimeService runtimeService;

    @EventListener
    private void processPostDeploy(PostDeployEvent event) {
        runtimeService.startProcessInstanceByKey("food");
    }
    // <<
}
```