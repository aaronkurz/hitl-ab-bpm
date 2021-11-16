package org.example.sbe_prototyping;

import com.camunda.consulting.simulator.PayloadGenerator;
import com.camunda.consulting.simulator.SimulationExecutor;
import com.camunda.consulting.simulator.SimulatorPlugin;
import org.camunda.bpm.engine.RuntimeService;
import org.camunda.bpm.spring.boot.starter.annotation.EnableProcessApplication;
import org.camunda.bpm.spring.boot.starter.event.PostDeployEvent;
import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.event.EventListener;

@SpringBootApplication
@EnableProcessApplication
public class WebappExampleProcessApplication {
    public static void main(String... args) {
        SpringApplication.run(WebappExampleProcessApplication.class, args);

    }

    @Autowired
    private RuntimeService runtimeService;

    @EventListener
    private void processPostDeploy(PostDeployEvent event) {
        runtimeService.startProcessInstanceByKey("food");
        SimulationExecutor.execute(DateTime.now().minusMonths(1).toDate(), DateTime.now().toDate());
    }

    @Bean
    public SimulatorPlugin simulatorPlugin() {
        return new SimulatorPlugin();
    }

    @Bean
    public PayloadGenerator generator() {
        return new PayloadGenerator();
    }
}