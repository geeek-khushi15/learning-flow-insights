from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import ClassSession, Attendance, SessionTopic, TopicAcknowledgement
from batches.models import Batch
from enrollments.models import Enrollment


@login_required
def create_session(request):
    if request.user.role != 'TRAINER':
        return redirect('dashboard')

    batches = Batch.objects.filter(trainer=request.user)

    if request.method == 'POST':
        batch_id = request.POST.get('batch')
        date = request.POST.get('date')
        topics_covered = request.POST.get('topics_covered', '').strip()

        batch = get_object_or_404(Batch, id=batch_id, trainer=request.user)

        # Create session
        session = ClassSession.objects.create(
            batch=batch,
            date=date,
            topics_covered=topics_covered,
            trainer=request.user
        )

        # Create attendance records
        enrollments = Enrollment.objects.filter(batch=batch)

        for enrollment in enrollments:
            Attendance.objects.get_or_create(
                session=session,
                student=enrollment.student
            )

        # Parse topics
        if topics_covered:
            import re

            topic_list = [
                t.strip()
                for t in re.split(r'[,\n]+', topics_covered)
                if t.strip()
            ]

            for topic in topic_list:

                s_topic = SessionTopic.objects.create(
                    session=session,
                    topic_name=topic
                )

                for enrollment in enrollments:

                    TopicAcknowledgement.objects.get_or_create(
                        session_topic=s_topic,
                        student=enrollment.student
                    )

        messages.success(
            request,
            f"Class session and topics successfully logged for {batch.name}."
        )

        return redirect('trainer_session_list')

    return render(
        request,
        'attendance/create_session.html',
        {'batches': batches}
    )


@login_required
def mark_attendance(request, session_id):

    if request.user.role != 'TRAINER':
        return redirect('dashboard')

    session = get_object_or_404(
        ClassSession,
        id=session_id,
        trainer=request.user
    )

    attendances = session.attendances.all().select_related('student')

    if request.method == 'POST':

        for attendance in attendances:

            student_id = str(attendance.student.id)

            is_present = request.POST.get(
                f'attendance_{student_id}'
            ) == 'on'

            attendance.is_present = is_present
            attendance.save()

        messages.success(
            request,
            f"Attendance successfully updated for {session.date}."
        )

        return redirect('trainer_session_list')

    return render(
        request,
        'attendance/mark_attendance.html',
        {
            'session': session,
            'attendances': attendances
        }
    )


@login_required
def trainer_session_list(request):

    if request.user.role != 'TRAINER':
        return redirect('dashboard')

    sessions = ClassSession.objects.filter(
        trainer=request.user
    ).select_related('batch').order_by('-date')

    return render(
        request,
        'attendance/trainer_session_list.html',
        {'sessions': sessions}
    )


@login_required
def manage_session_topics(request, session_id):

    if request.user.role != 'TRAINER':
        return redirect('dashboard')

    session = get_object_or_404(
        ClassSession,
        id=session_id,
        trainer=request.user
    )

    topics = session.topics.all()

    if request.method == 'POST':

        for topic in topics:

            if not topic.trainer_taught:

                topic_id = str(topic.id)

                taught = request.POST.get(
                    f'taught_{topic_id}'
                ) == 'on'

                if taught:
                    topic.trainer_taught = True
                    topic.taught_at = timezone.now()
                    topic.save()

        messages.success(
            request,
            f"Topics status updated for {session.date}."
        )

        return redirect('trainer_session_list')

    return render(
        request,
        'attendance/manage_session_topics.html',
        {
            'session': session,
            'topics': topics
        }
    )


@login_required
def student_session_list(request):

    if request.user.role != 'STUDENT':
        return redirect('dashboard')

    attendances = Attendance.objects.filter(
        student=request.user,
        is_present=True
    ).select_related(
        'session',
        'session__batch',
        'session__trainer'
    ).order_by('-session__date')

    sessions = [a.session for a in attendances]

    return render(
        request,
        'attendance/student_session_list.html',
        {'sessions': sessions}
    )


@login_required
def student_acknowledge_topics(request, session_id):

    if request.user.role != 'STUDENT':
        return redirect('dashboard')

    session = get_object_or_404(ClassSession, id=session_id)

    attendance = Attendance.objects.filter(
        session=session,
        student=request.user
    ).first()

    if not attendance or not attendance.is_present:

        messages.error(
            request,
            "You cannot view topics for a session you were marked absent from."
        )

        return redirect('student_session_list')

    acknowledgements = TopicAcknowledgement.objects.filter(
        session_topic__session=session,
        student=request.user
    ).select_related('session_topic')

    if request.method == 'POST':

        for ack in acknowledgements:

            ack_id = str(ack.id)

            understood = request.POST.get(
                f'understood_{ack_id}'
            ) == 'on'

            # IMPORTANT SECURITY CHECK
            # Student can acknowledge ONLY if trainer verified topic

            if (
                understood
                and not ack.student_understood
                and ack.session_topic.trainer_taught
            ):

                ack.student_understood = True
                ack.understood_at = timezone.now()
                ack.save()

        messages.success(
            request,
            "Topic acknowledgements successfully updated."
        )

        return redirect('student_session_list')

    return render(
        request,
        'attendance/student_acknowledge_topics.html',
        {
            'session': session,
            'acknowledgements': acknowledgements
        }
    )